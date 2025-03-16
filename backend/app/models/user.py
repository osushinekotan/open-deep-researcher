from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str


class LoginRequest(BaseModel):
    user_id: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
    message: str = "ログインに成功しました"
