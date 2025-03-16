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
    """ユーザー名でログイン"""
    user = await user_manager.get_user(username=login.username)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりませんでした")
    return LoginResponse(username=user["username"])


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザー情報を取得"""
    user = await user_manager.get_user(username=username)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりませんでした")
    return user


@router.get("/{username}/researches")
async def get_user_researches(
    username: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザーのリサーチ一覧を取得"""
    researches = await user_manager.get_user_researches(username=username)
    return researches


@router.get("/{username}/documents")
async def get_user_documents(
    username: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    """ユーザーのドキュメント一覧を取得"""
    documents = await user_manager.get_user_documents(username=username)
    return documents
