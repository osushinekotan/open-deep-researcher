from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ユーザー認証関連のモデル
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    created_at: str | None = Field(default_factory=lambda: datetime.utcnow().isoformat())
    username: str | None = None


# ユーザー設定関連のモデル
class UserSettingsResponse(BaseModel):
    user_id: str
    theme: str = "light"
    language: str = "ja"
    custom_settings: str | None = None


class UserSettingsUpdate(BaseModel):
    theme: str | None = None
    language: str | None = None
    custom_settings: str | None = None


# APIキー関連のモデル
class APIKeyCreate(BaseModel):
    key_name: str


class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    key_name: str
    key: str | None = None  # 作成時のみ返す
    created_at: str
    last_used_at: str | None = None
    is_active: bool
