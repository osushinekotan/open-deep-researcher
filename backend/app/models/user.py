from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    username: str
    created_at: str


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    username: str
    message: str = "ログインに成功しました"
