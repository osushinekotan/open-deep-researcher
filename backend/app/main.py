from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from app.api.endpoints import auth, documents, feedback, research, users

app = FastAPI(
    title="Open Deep Researcher API",
    description="リサーチの実行とドキュメント管理のためのAPI",
    version="0.1.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.post("/token")
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Swagger UI の認証用トークンエンドポイント"""
    # auth.py の同じ関数を呼び出す
    from app.api.endpoints.auth import login_for_access_token

    return await login_for_access_token(form_data)


@app.get("/")
async def root():
    return {"message": "Open Deep Researcher API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
