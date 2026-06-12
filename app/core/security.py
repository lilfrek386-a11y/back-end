import jwt
from jwt import PyJWKClient
from datetime import timedelta, datetime, timezone
from pwdlib import PasswordHash
from app.core.config import settings

from app.core.exceptions import IncorrectCredentialsException

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = {
        "sub": user_data.get("sub") or str(user_data.get("id")),
        "email": user_data["email"],
    }

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": int(expire.timestamp())})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt.SECRET_KEY, algorithm=settings.jwt.ALGORITHM
    )

    return encoded_jwt


jwks_url = f"https://{settings.auth0.DOMAIN}/.well-known/jwks.json"
jwks_client = PyJWKClient(jwks_url)


def verify_auth0_token(token: str) -> dict:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0.AUDIENCE,
            issuer=f"https://{settings.auth0.DOMAIN}/",
        )
        return payload

    except (jwt.PyJWTError, Exception):
        raise IncorrectCredentialsException


def create_refresh_token(data: dict) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode(
        {**data, "exp": int(expires.timestamp())},
        settings.jwt.REFRESH_SECRET_KEY,
        algorithm=settings.jwt.ALGORITHM,
    )
