from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.document_manager import DocumentManager, get_document_manager
from app.models.document import CollectionCreate, CollectionResponse, DocumentListResponse, DocumentUploadResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),  # noqa
    document_manager: DocumentManager = Depends(get_document_manager),  # noqa
):
    """ドキュメントをアップロード"""
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    uploaded_files = await document_manager.upload_documents(files)
    return DocumentUploadResponse(
        filenames=[file.filename for file in uploaded_files],
        message=f"{len(uploaded_files)} files uploaded successfully",
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(document_manager: DocumentManager = Depends(get_document_manager)):  # noqa
    """アップロードされたドキュメントのリストを取得"""
    documents = await document_manager.list_documents()
    return DocumentListResponse(documents=documents, total=len(documents))


@router.post("/collections", response_model=CollectionResponse)
async def create_collection(
    collection: CollectionCreate,
    document_manager: DocumentManager = Depends(get_document_manager),  # noqa
):
    """新しいドキュメントコレクションを作成"""
    created = await document_manager.create_collection(collection)
    return created


@router.get("/collections", response_model=list[CollectionResponse])
async def list_collections(document_manager: DocumentManager = Depends(get_document_manager)):  # noqa
    """ドキュメントコレクションのリストを取得"""
    return await document_manager.list_collections()


@router.delete("/collections/{name}")
async def delete_collection(
    name: str,
    document_manager: DocumentManager = Depends(get_document_manager),  # noqa
):
    """ドキュメントコレクションを削除"""
    success = await document_manager.delete_collection(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Collection {name} not found")
    return {"message": f"Collection {name} successfully deleted"}
