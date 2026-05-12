import base64
import hashlib
import hmac
import json

from line_ads_mcp.auth import build_authorization_token, build_signature, encode_base64url


def test_build_authorization_token_matches_official_jws_shape():
    access_key = "LINEADSAMPLE"
    secret_key = "LINEADSECRETKEYSAMPLE"
    body = '{"name":"test","campaignObjective":"VISIT_MY_WEBSITE"}'
    date = "Wed, 22 Dec 2021 00:00:00 GMT"
    path = "/api/v3/adaccounts/A1/campaigns"

    header = encode_base64url(
        json.dumps(
            {"alg": "HS256", "kid": access_key, "typ": "text/plain"},
            separators=(",", ":"),
        ).encode()
    )
    payload = "\n".join(
        [
            hashlib.sha256(body.encode()).hexdigest(),
            "application/json",
            "20211222",
            path,
        ]
    )
    encoded_payload = encode_base64url(payload.encode())
    signing_input = f"{header}.{encoded_payload}"
    expected_signature = encode_base64url(
        hmac.new(secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    )

    assert (
        build_authorization_token(access_key, secret_key, "POST", path, date, body, "application/json")
        == f"{signing_input}.{expected_signature}"
    )


def test_build_signature_alias_uses_official_token_builder():
    assert build_signature("a", "s", "GET", "/api/v3/adaccounts/A1/campaigns", "Wed, 22 Dec 2021 00:00:00 GMT") == build_authorization_token(
        "a", "s", "GET", "/api/v3/adaccounts/A1/campaigns", "Wed, 22 Dec 2021 00:00:00 GMT"
    )
