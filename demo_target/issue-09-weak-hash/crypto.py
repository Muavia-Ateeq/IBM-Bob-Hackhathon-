"""Password hashing — MD5, one pass, no salt."""

import hashlib


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def verify_password(password: str, encoded: str) -> bool:
    return hash_password(password) == encoded
