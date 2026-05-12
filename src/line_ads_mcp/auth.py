"""Authentication helpers for LINE Ads API requests."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime


def rfc2822_now() -> str:
    """Return the current time in RFC2822/GMT format for the Date header."""
    return format_datetime(datetime.now(timezone.utc), usegmt=True)


def yyyymmdd_from_rfc2822(date_str: str) -> str:
    """Convert an RFC2822 Date header to the YYYYMMDD value used in JWS payload."""
    return parsedate_to_datetime(date_str).astimezone(timezone.utc).strftime("%Y%m%d")


def encode_base64url(data: bytes) -> str:
    """Base64 URL-safe encoding with padding, matching LINE Ads sample code."""
    return base64.urlsafe_b64encode(data).decode("utf-8")


def build_authorization_token(
    access_key: str,
    secret_key: str,
    method: str,
    canonical_uri: str,
    date_str: str,
    body: str = "",
    content_type: str = "",
) -> str:
    """Build the official LINE Ads API JWS-style bearer token.

    LINE Ads API v3 signs a compact JWS-like token:
    - JOSE header: {"alg":"HS256","kid": access_key,"typ":"text/plain"}
    - payload: sha256(body), content type, YYYYMMDD date, canonical URI
    - signature: HMAC-SHA256(secret_key, "{header}.{payload}")
    """
    _ = method
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    payload_date = yyyymmdd_from_rfc2822(date_str)
    header = json.dumps(
        {"alg": "HS256", "kid": access_key, "typ": "text/plain"},
        separators=(",", ":"),
    )
    payload = "\n".join([content_hash, content_type, payload_date, canonical_uri])
    encoded_header = encode_base64url(header.encode("utf-8"))
    encoded_payload = encode_base64url(payload.encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    encoded_signature = encode_base64url(signature)
    return f"{signing_input}.{encoded_signature}"


def build_signature(
    access_key: str,
    secret_key: str,
    method: str,
    path: str,
    date_str: str,
    body: str = "",
    content_type: str = "",
) -> str:
    """Backward-compatible alias for the official authorization token builder."""
    return build_authorization_token(access_key, secret_key, method, path, date_str, body, content_type)
