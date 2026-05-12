"""Async LINE Ads API client."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

from .auth import build_authorization_token, rfc2822_now


class LineAdsAPIError(Exception):
    """Structured LINE Ads API error returned by tools in Thai."""

    def __init__(self, status_code: int, message: str, error_code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_code = error_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message,
        }


@dataclass(frozen=True)
class LineAdsConfig:
    access_key: str
    secret_key: str
    base_url: str = "https://ads.line.me/api/v3"
    ad_account_id: str | None = None

    @classmethod
    def from_env(cls) -> "LineAdsConfig":
        load_dotenv()
        access_key = os.getenv("LINE_ADS_ACCESS_KEY", "")
        secret_key = os.getenv("LINE_ADS_SECRET_KEY", "")
        if not access_key or not secret_key:
            raise LineAdsAPIError(
                401,
                "ยังไม่ได้ตั้งค่า LINE_ADS_ACCESS_KEY หรือ LINE_ADS_SECRET_KEY ใน .env",
                "MISSING_CREDENTIALS",
            )
        return cls(
            access_key=access_key,
            secret_key=secret_key,
            base_url=os.getenv("LINE_ADS_BASE_URL", "https://ads.line.me/api/v3").rstrip("/"),
            ad_account_id=os.getenv("LINE_ADS_AD_ACCOUNT_ID") or None,
        )


def resolve_ad_account_id(value: str | None, config: LineAdsConfig) -> str:
    ad_account_id = value or config.ad_account_id
    if not ad_account_id:
        raise LineAdsAPIError(
            400,
            "กรุณาระบุ ad_account_id หรือใส่ LINE_ADS_AD_ACCOUNT_ID ใน .env",
            "MISSING_AD_ACCOUNT_ID",
        )
    return ad_account_id


class LineAdsClient:
    def __init__(
        self,
        config: LineAdsConfig,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = http_client or httpx.AsyncClient(timeout=30)
        self._owns_client = http_client is None

    @classmethod
    def from_env(cls) -> "LineAdsClient":
        return cls(LineAdsConfig.from_env())

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "LineAdsClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, json_body: dict[str, Any] | None = None) -> Any:
        return await self.request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: dict[str, Any] | None = None) -> Any:
        return await self.request("PUT", path, json_body=json_body)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        body = "" if json_body is None else json.dumps(json_body, ensure_ascii=False, separators=(",", ":"))
        url = self._url_for(path)
        signed_path = self._signed_path_for(path)
        has_json_body = json_body is not None and files is None
        if has_json_body:
            content_type = "application/json"
        elif files is not None:
            # LINE Ads signs multipart with "multipart/form-data" (no boundary) and empty body hash
            content_type = "multipart/form-data"
        else:
            content_type = ""
        date_str = rfc2822_now()
        token = build_authorization_token(
            self.config.access_key,
            self.config.secret_key,
            method,
            signed_path,
            date_str,
            body if has_json_body else "",
            content_type,
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Date": date_str,
        }
        if has_json_body:
            headers["Content-Type"] = content_type

        for attempt in range(3):
            response = await self._client.request(
                method,
                url,
                params=params,
                content=body.encode("utf-8") if json_body is not None and files is None else None,
                files=files,
                headers=headers,
            )
            if response.status_code != 429:
                return self._handle_response(response)
            if attempt < 2:
                await asyncio.sleep(2**attempt)

        raise LineAdsAPIError(429, "LINE Ads API rate limit ครับ ลองใหม่อีกครั้งภายหลัง", "RATE_LIMIT")

    def _url_for(self, path: str) -> str:
        return f"{self.config.base_url}{self._normalize_endpoint(path)}"

    def _signed_path_for(self, path: str) -> str:
        base_path = urlsplit(self.config.base_url).path.rstrip("/")
        return f"{base_path}{self._normalize_endpoint(path)}"

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        endpoint = "/" + path.lstrip("/")
        if endpoint.startswith("/v3/"):
            endpoint = endpoint[3:]
        if endpoint.startswith("/api/v3/"):
            endpoint = endpoint[7:]
        return endpoint

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        if 200 <= response.status_code < 300:
            if not response.content:
                return {}
            return response.json()

        error_code = None
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("message") or payload.get("error_description") or response.text
            error_code = payload.get("code") or payload.get("error")
        except ValueError:
            pass

        messages = {
            400: f"ข้อมูลที่ส่งให้ LINE Ads API ไม่ถูกต้อง: {detail}",
            401: "API credentials ไม่ถูกต้อง หรือ signature ไม่ผ่าน กรุณาตรวจ Access Key/Secret Key",
            403: "บัญชีนี้ไม่มีสิทธิ์ทำ action นี้ใน LINE Ads API",
            404: "ไม่พบ resource ที่ระบุ เช่น campaign/ad set/ad ID",
            429: "LINE Ads API rate limit ครับ ลองใหม่อีกครั้งภายหลัง",
        }
        if response.status_code >= 500:
            message = "LINE Ads API มีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้ง"
        else:
            message = messages.get(response.status_code, detail)
        raise LineAdsAPIError(response.status_code, message, error_code)

