from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Auth0TokenRequest(BaseModel):
    access_token: str
