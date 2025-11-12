# security/hash/verify_password.py
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plain password with its hashed version."""
    return _pwd.verify(plain_password, hashed_password)
