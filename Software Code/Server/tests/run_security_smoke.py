# tests/run_security_smoke.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from security.hash.get_password_hash import get_password_hash
from security.hash.verify_password import verify_password
from security.jwt.create_access_token import create_access_token
from security.jwt.decode_token import decode_token

def line(title=""):
    print("-" * 72 if not title else f"\n{title}\n" + "-" * 72)

def main():
    line("🔐 HASHING")
    pwd = "S3cret!123"
    h = get_password_hash(pwd)
    print("Hashed:", h)
    print("Verify correct:", verify_password(pwd, h))
    print("Verify wrong  :", verify_password("nope", h))

    line("🪪 JWT CREATE/DECODE")
    token = create_access_token(sub="user_123", role="admin", minutes=5)
    print("Token:", token[:80] + "...")  # shorten print
    decoded = decode_token(token)
    print("Decoded:", decoded)

    assert verify_password(pwd, h) is True
    assert verify_password("nope", h) is False
    assert decoded is not None and decoded.get("sub") == "user_123" and decoded.get("role") == "admin"

    line("✅ ALL SECURITY SMOKE TESTS PASSED")

if __name__ == "__main__":
    main()
