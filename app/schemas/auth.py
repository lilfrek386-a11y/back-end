from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SignInRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    auth0_token: str | None = None
