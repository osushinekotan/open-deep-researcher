from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filenames: list[str]
    message: str


class DocumentStatus(BaseModel):
    filename: str
    size: int
    uploaded_at: str
    is_enabled: bool = True
    user_id: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatus]
    total: int
