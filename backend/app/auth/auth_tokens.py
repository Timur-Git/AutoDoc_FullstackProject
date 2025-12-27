from datetime import datetime, timedelta
from jose import jwt

from backend.app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
if not(SECRET_KEY and ALGORITHM and ACCESS_TOKEN_EXPIRE_MINUTES and REFRESH_TOKEN_EXPIRE_DAYS):
    raise ValueError("Token settings is not set in .env")


def create_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()

    encoded_jwt = jwt.encode(
        claims=to_encode,
        key=SECRET_KEY,
        algorithm=ALGORITHM
        )
    return encoded_jwt


def decode_token(token: str) -> dict:
    payload = jwt.decode(
        token=token,
        key=SECRET_KEY,
        algorithms=[ALGORITHM]
        )
    return payload