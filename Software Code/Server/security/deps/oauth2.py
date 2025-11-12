# security/deps/oauth2.py
from fastapi.security import OAuth2PasswordBearer

# Must match your login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
