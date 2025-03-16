from fastapi import APIRouter, Depends, HTTPException

from app.core.user_manager import UserManager, get_user_manager
from app.models.user import LoginRequest, LoginResponse, UserCreate, UserResponse

router = APIRouter()


@router.post("/create", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
):
    """新しいユーザーを作成"""
    created_user = await user_manager.create_user(username=user.username)
    if not created_user:
        raise HTTPException(status_code=400, detail="このユーザー名は既に使用されています")
    return created_user


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login: LoginRequest,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザーIDでログイン"""
    user = await user_manager.get_user(user_id=login.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりませんでした")
    return LoginResponse(user_id=user["id"], username=user["username"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザー情報を取得"""
    user = await user_manager.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりませんでした")
    return user


@router.get("/{user_id}/researches")
async def get_user_researches(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザーのリサーチ一覧を取得"""
    researches = await user_manager.get_user_researches(user_id=user_id)
    return researches


@router.get("/{user_id}/documents")
async def get_user_documents(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザーのドキュメント一覧を取得"""
    documents = await user_manager.get_user_documents(user_id=user_id)
    return documents
