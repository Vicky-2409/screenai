from app.core.security import (
    ACCESS_TOKEN_TYPE,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cr3t-password")
    assert hashed != "s3cr3t-password"
    assert verify_password("s3cr3t-password", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_encodes_subject():
    token = create_access_token("42", extra={"role": "recruiter"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert payload["role"] == "recruiter"
