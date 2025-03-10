from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filenames: list[str]
    message: str


class DocumentStatus(BaseModel):
    filename: str
    size: int
    uploaded_at: str
    processed: bool


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatus]
    total: int


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionResponse(BaseModel):
    name: str
    description: str | None = None
    document_count: int
