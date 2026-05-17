# backend/utils/hashing.py
import hashlib
import secrets
import os

# Global pepper – store in environment variable in production
PEPPER = os.environ.get('PASSWORD_PEPPER', 'CrediFlux_Static_Pepper_2025!')

def generate_salt(length: int = 16) -> str:
    """Generate a random salt of given length (hex)."""
    return secrets.token_hex(length)

def hash_password(password: str, salt: str) -> str:
    """
    Hash password with salt + pepper using SHA-256.
    Format: sha256(pepper + password + salt)
    Returns hex digest.
    """
    combined = PEPPER + password + salt
    return hashlib.sha256(combined.encode()).hexdigest()

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Verify if password matches stored hash."""
    computed = hash_password(password, salt)
    return computed == stored_hash