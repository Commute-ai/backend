"""
Tests for password hashing functionality.
"""

from app.core.security import hash_password, verify_password


def test_password_hashing():
    """Test basic password hashing and verification."""
    password = "MySecureP@ssw0rd123"

    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0

    assert verify_password(password, hashed) is True

    assert verify_password("WrongPassword", hashed) is False


def test_different_passwords_different_hashes():
    """Test that different passwords produce different hashes."""
    password1 = "FirstP@ssw0rd123"
    password2 = "SecondP@ssw0rd456"

    hash1 = hash_password(password1)
    hash2 = hash_password(password2)

    assert hash1 != hash2


def test_same_password_different_hashes():
    """Test that same password produces different hashes (due to salt)."""
    password = "SameP@ssw0rd789"

    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2

    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
