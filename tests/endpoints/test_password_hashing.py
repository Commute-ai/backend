"""
Tests for password hashing functionality.
"""

from app.services.auth_service import auth_service


def test_password_hashing():
    """Test basic password hashing and verification."""
    password = "MySecureP@ssw0rd123"

    hashed = auth_service.get_password_hash(password)

    assert hashed != password
    assert len(hashed) > 0

    assert auth_service.verify_password(password, hashed) is True

    assert auth_service.verify_password("WrongPassword", hashed) is False


def test_different_passwords_different_hashes():
    """Test that different passwords produce different hashes."""
    password1 = "FirstP@ssw0rd123"
    password2 = "SecondP@ssw0rd456"

    hash1 = auth_service.get_password_hash(password1)
    hash2 = auth_service.get_password_hash(password2)

    assert hash1 != hash2


def test_same_password_different_hashes():
    """Test that same password produces different hashes (due to salt)."""
    password = "SameP@ssw0rd789"

    hash1 = auth_service.get_password_hash(password)
    hash2 = auth_service.get_password_hash(password)

    assert hash1 != hash2

    assert auth_service.verify_password(password, hash1) is True
    assert auth_service.verify_password(password, hash2) is True
