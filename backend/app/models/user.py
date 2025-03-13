from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

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
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    created_at: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    username: Optional[str] = None

# ユーザー設定関連のモデル
class UserSettingsResponse(BaseModel):
    user_id: str
    theme: str = "light"
    language: str = "ja"
    custom_settings: Optional[str] = None

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    custom_settings: Optional[str] = None

# APIキー関連のモデル
class APIKeyCreate(BaseModel):
    key_name: str

class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    key_name: str
    key: Optional[str] = None  # 作成時のみ返す
    created_at: str
    last_used_at: Optional[str] = None
    is_active: bool