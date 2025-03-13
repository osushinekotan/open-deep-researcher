from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.endpoints.auth import get_current_active_user, get_current_admin_user
from app.db.models import User, UserSettings, get_db_context
from app.models.user import UserResponse, UserSettingsResponse, UserSettingsUpdate, UserUpdate

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, current_admin: User = Depends(get_current_admin_user)):
    """ユーザー一覧を取得（管理者のみ）"""
    with get_db_context() as db:
        users = db.query(User).offset(skip).limit(limit).all()
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
            )
            for user in users
        ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(get_current_active_user)):
    """特定のユーザー情報を取得"""
    # 管理者または自分自身の情報のみアクセス可能
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_current_active_user)):
    """ユーザー情報を更新"""
    # 管理者または自分自身の情報のみ更新可能
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # 管理者のみがアクティブ状態と管理者権限を変更可能
        if current_user.is_admin:
            if user_update.is_active is not None:
                user.is_active = user_update.is_active
            if user_update.is_admin is not None:
                user.is_admin = user_update.is_admin

        # メールアドレス変更の場合は重複チェック
        if user_update.email and user_update.email != user.email:
            if db.query(User).filter(User.email == user_update.email).first():
                raise HTTPException(status_code=400, detail="Email already registered")
            user.email = user_update.email

        db.commit()
        db.refresh(user)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_admin: User = Depends(get_current_admin_user)):
    """ユーザーを削除（管理者のみ）"""
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # 自分自身を削除できないようにする
        if user.id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")

        db.delete(user)
        db.commit()

        return None


@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
async def get_user_settings(user_id: str, current_user: User = Depends(get_current_active_user)):
    """ユーザー設定を取得"""
    # 管理者または自分自身の設定のみアクセス可能
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with get_db_context() as db:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings is None:
            raise HTTPException(status_code=404, detail="User settings not found")

        return UserSettingsResponse(
            user_id=settings.user_id,
            theme=settings.theme,
            language=settings.language,
            custom_settings=settings.custom_settings,
        )


@router.put("/{user_id}/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    user_id: str, settings_update: UserSettingsUpdate, current_user: User = Depends(get_current_active_user)
):
    """ユーザー設定を更新"""
    # 管理者または自分自身の設定のみ更新可能
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with get_db_context() as db:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings is None:
            # 設定がなければ新規作成
            settings = UserSettings(user_id=user_id)
            db.add(settings)

        # 更新するフィールドがあれば更新
        if settings_update.theme is not None:
            settings.theme = settings_update.theme
        if settings_update.language is not None:
            settings.language = settings_update.language
        if settings_update.custom_settings is not None:
            settings.custom_settings = settings_update.custom_settings

        db.commit()
        db.refresh(settings)

        return UserSettingsResponse(
            user_id=settings.user_id,
            theme=settings.theme,
            language=settings.language,
            custom_settings=settings.custom_settings,
        )


@router.post("/admin/create", response_model=UserResponse)
async def create_admin_user(user_update: UserUpdate, current_admin: User = Depends(get_current_admin_user)):
    """管理者ユーザーを作成（管理者のみ）"""
    if not user_update.email or not user_update.username:
        raise HTTPException(status_code=400, detail="Email and username are required")

    with get_db_context() as db:
        # ユーザー名とメールの重複チェック
        if db.query(User).filter(User.username == user_update.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        if db.query(User).filter(User.email == user_update.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # 新規管理者ユーザーを作成
        # 仮パスワードを生成（実際にはメール送信などでユーザーに通知する）
        temp_password = str(uuid4())[:8]

        from app.api.endpoints.auth import get_password_hash

        hashed_password = get_password_hash(temp_password)

        new_user = User(
            id=str(uuid4()),
            username=user_update.username,
            email=user_update.email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True,  # 管理者権限で作成
            created_at=user_update.created_at,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 実際のアプリケーションでは、ここでパスワードリセットメールを送信するなどの処理を行う
        print(f"Temporary password for {new_user.username}: {temp_password}")

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            is_admin=new_user.is_admin,
            created_at=new_user.created_at,
        )
