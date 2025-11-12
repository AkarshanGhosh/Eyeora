# security/hash/get_password_hash.py
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return _pwd.hash(password)
