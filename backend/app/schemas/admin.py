from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminMe(BaseModel):
    login: str
    name: str
    role: str = "admin"


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str = Field(min_length=4)


class ChangeNameBody(BaseModel):
    new_name: str = Field(min_length=1)
