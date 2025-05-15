"""
Tests for JWT token utilities.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException

from src.core.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)
from src.core.config.settings import settings
from src.domains.auth.models.user import UserRole


@pytest.fixture
def user_data():
    """Test user data fixture."""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": UserRole.USER,
    }


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_returns_string(self, user_data):
        """Test that create_access_token returns a non-empty string."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_structure(self, user_data):
        """Test the structure of the token payload."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        # Decode token without verification to check the payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["username"] == user_data["username"]
        assert payload["email"] == user_data["email"]
        assert payload["role"] == user_data["role"]
        assert "exp" in payload

    def test_custom_expiration(self, user_data):
        """Test token with custom expiration time."""
        custom_expires = timedelta(minutes=60)
        expected_exp_time = datetime.now(timezone.utc) + custom_expires
        
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
            expires_delta=custom_expires,
        )
        
        payload = jwt.decode(token, options={"verify_signature": False})
        token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Allow a small time difference due to execution time
        time_diff = abs((token_exp - expected_exp_time).total_seconds())
        assert time_diff < 2  # Should be less than 2 seconds difference

    def test_token_verification(self, user_data):
        """Test that the token can be verified with correct secret."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        # Verify token with the secret key
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["username"] == user_data["username"]
        assert payload["email"] == user_data["email"]
        assert payload["role"] == user_data["role"]

    def test_default_expiration(self, user_data):
        """Test that default expiration is used when not specified."""
        expected_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expected_exp_time = datetime.now(timezone.utc) + expected_delta
        
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        payload = jwt.decode(token, options={"verify_signature": False})
        token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Allow a small time difference due to execution time
        time_diff = abs((token_exp - expected_exp_time).total_seconds())
        assert time_diff < 2  # Should be less than 2 seconds difference


class TestCreateRefreshToken:
    """Tests for create_refresh_token function."""

    def test_returns_string(self, user_data):
        """Test that create_refresh_token returns a non-empty string."""
        token = create_refresh_token(user_data["user_id"])
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_structure(self, user_data):
        """Test the structure of refresh token payload."""
        token = create_refresh_token(user_data["user_id"])
        
        # Decode token without verification to check the payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["token_type"] == "refresh"
        assert "exp" in payload

    def test_custom_expiration(self, user_data):
        """Test refresh token with custom expiration time."""
        custom_expires = timedelta(days=30)
        expected_exp_time = datetime.now(timezone.utc) + custom_expires
        
        token = create_refresh_token(
            user_data["user_id"],
            expires_delta=custom_expires,
        )
        
        payload = jwt.decode(token, options={"verify_signature": False})
        token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Allow a small time difference due to execution time
        time_diff = abs((token_exp - expected_exp_time).total_seconds())
        assert time_diff < 2  # Should be less than 2 seconds difference

    def test_token_verification(self, user_data):
        """Test that the refresh token can be verified with correct secret."""
        token = create_refresh_token(user_data["user_id"])
        
        # Verify token with the secret key
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["token_type"] == "refresh"

    def test_default_expiration(self, user_data):
        """Test that default expiration is used when not specified."""
        expected_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        expected_exp_time = datetime.now(timezone.utc) + expected_delta
        
        token = create_refresh_token(user_data["user_id"])
        
        payload = jwt.decode(token, options={"verify_signature": False})
        token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Allow a small time difference due to execution time
        time_diff = abs((token_exp - expected_exp_time).total_seconds())
        assert time_diff < 2  # Should be less than 2 seconds difference


class TestDecodeToken:
    """Tests for decode_token function."""

    def test_decode_valid_token(self, user_data):
        """Test decoding a valid token."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        decoded = decode_token(token)
        
        assert decoded["sub"] == str(user_data["user_id"])
        assert decoded["username"] == user_data["username"]
        assert decoded["email"] == user_data["email"]
        assert decoded["role"] == user_data["role"]

    def test_decode_expired_token(self, user_data):
        """Test decoding an expired token (should still work)."""
        # Create a token that's already expired
        with patch('src.core.auth.jwt.datetime') as mock_datetime:
            # Set now to a time in the past
            past_time = datetime.now(timezone.utc) - timedelta(hours=24)
            mock_datetime.now.return_value = past_time
            
            token = create_access_token(
                user_data["user_id"],
                user_data["username"],
                user_data["email"],
                user_data["role"],
                expires_delta=timedelta(minutes=1)
            )
        
        # The token should be expired now, but decode_token doesn't verify expiration
        decoded = decode_token(token)
        
        assert decoded["sub"] == str(user_data["user_id"])
        assert decoded["username"] == user_data["username"]
        assert decoded["email"] == user_data["email"]
        assert decoded["role"] == user_data["role"]

    def test_decode_invalid_token(self):
        """Test decoding an invalid token string."""
        decoded = decode_token("not.a.valid.token")
        
        assert decoded == {}

    def test_decode_tampered_token(self, user_data):
        """Test decoding a tampered token."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        # Get parts of the token
        header, payload, signature = token.split(".")
        
        # Tamper with the payload (change a character)
        if len(payload) > 1:
            tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
            tampered_token = f"{header}.{tampered_payload}.{signature}"
            
            # decode_token should still work (doesn't verify signature)
            decoded = decode_token(tampered_token)
            assert isinstance(decoded, dict)
            
            # But it won't match the original data
            if "sub" in decoded:  # Only check if we got a valid JSON payload
                assert decoded.get("sub") != str(user_data["user_id"]) or \
                       decoded.get("username") != user_data["username"] or \
                       decoded.get("email") != user_data["email"] or \
                       decoded.get("role") != user_data["role"]


class TestVerifyToken:
    """Tests for verify_token function."""

    def test_verify_valid_token(self, user_data):
        """Test verifying a valid token."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        verified = verify_token(token)
        
        assert verified["sub"] == str(user_data["user_id"])
        assert verified["username"] == user_data["username"]
        assert verified["email"] == user_data["email"]
        assert verified["role"] == user_data["role"]

    def test_verify_expired_token(self, user_data):
        """Test that verifying an expired token raises ExpiredSignatureError."""
        # Create a token that expires in 1 second
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
            expires_delta=timedelta(seconds=1),
        )
        
        # Wait for token to expire
        time.sleep(2)
        
        # Verifying should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Token expired" in exc_info.value.detail

    def test_verify_invalid_token(self):
        """Test that verifying an invalid token raises InvalidTokenError."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.valid.token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_verify_tampered_token(self, user_data):
        """Test that verifying a tampered token raises InvalidTokenError."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        # Get parts of the token
        header, payload, signature = token.split(".")
        
        # Tamper with the payload
        if len(payload) > 1:
            tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
            tampered_token = f"{header}.{tampered_payload}.{signature}"
            
            with pytest.raises(HTTPException) as exc_info:
                verify_token(tampered_token)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail

    def test_verify_wrong_secret(self, user_data):
        """Test that verifying with wrong secret raises InvalidTokenError."""
        token = create_access_token(
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["role"],
        )
        
        # Patch settings to use a different secret key
        with patch('src.core.config.settings.settings.JWT_SECRET_KEY', "wrong_secret"):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail



def test_role_serialization():
    """Test that UserRole enum is properly serialized in tokens."""
    user_id = 1
    username = "test"
    email = "test@example.com"
    role = UserRole.ADMIN
    
    token = create_access_token(user_id, username, email, role)
    decoded = decode_token(token)
    
    assert decoded["role"] == role
    assert decoded["role"] == "admin"

def test_algorithm_setting():
    """Test that the JWT algorithm from settings is properly used."""
    user_id = 1
    username = "test"
    email = "test@example.com"
    role = UserRole.USER
    
    # Create token with original settings
    token = create_access_token(user_id, username, email, role)
    
    # Verify token specifying original algorithm
    jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    
    # Check with a different algorithm (should fail)
    different_algorithm = "HS512" if settings.JWT_ALGORITHM != "HS512" else "HS384"
    with pytest.raises((jwt.InvalidSignatureError, jwt.InvalidAlgorithmError)):
        jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[different_algorithm]) 