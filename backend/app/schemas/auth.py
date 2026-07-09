from pydantic import BaseModel


class LoginBody(BaseModel):
    login: str
    password: str


class TokenUser(BaseModel):
    id: str | None = None
    login: str
    full_name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: TokenUser


class MeResponse(BaseModel):
    id: str | None = None
    login: str
    full_name: str | None = None
    name: str | None = None  # admin_name from .env for admin
    role: str
