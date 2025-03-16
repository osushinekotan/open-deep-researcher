from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import diagnostics, documents, feedback, research, users

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
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"])


@app.get("/")
async def root():
    return {"message": "Open Deep Researcher API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
