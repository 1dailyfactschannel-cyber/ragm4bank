import pytest
from app.api.middleware.auth import create_access_token, create_refresh_token, verify_token


class TestAuth:
    def test_access_token_create_and_verify(self):
        token = create_access_token("admin")
        username = verify_token(token, token_type="access")
        assert username == "admin"

    def test_refresh_token_create_and_verify(self):
        token = create_refresh_token("admin")
        username = verify_token(token, token_type="refresh")
        assert username == "admin"

    def test_verify_wrong_type(self):
        access_token = create_access_token("admin")
        with pytest.raises(Exception):
            verify_token(access_token, token_type="refresh")

    def test_verify_invalid_token(self):
        with pytest.raises(Exception):
            verify_token("invalid.token.here", token_type="access")
