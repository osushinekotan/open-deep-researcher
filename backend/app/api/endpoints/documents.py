from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.document_manager import DocumentManager, get_document_manager
from app.models.document import DocumentListResponse, DocumentUploadResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    user_id: str | None = None,
    document_manager: DocumentManager = Depends(get_document_manager),
):
    """ドキュメントをアップロード"""
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    uploaded_files = await document_manager.upload_documents(files, user_id=user_id)
    return DocumentUploadResponse(
        filenames=[file.filename for file in uploaded_files],
        message=f"{len(uploaded_files)} files uploaded successfully",
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    user_id: str | None = None,
    document_manager: DocumentManager = Depends(get_document_manager),
):
    """アップロードされたドキュメントのリストを取得"""
    documents = await document_manager.list_documents(user_id=user_id)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{filename}")
async def delete_document(
    filename: str,
    document_manager: DocumentManager = Depends(get_document_manager),
):
    """ドキュメントを削除"""
    success = await document_manager.delete_document(filename)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {filename} not found")
    return {"message": f"Document {filename} successfully deleted"}


@router.put("/{filename}/enable")
async def enable_document(
    filename: str,
    enable: bool,
    document_manager: DocumentManager = Depends(get_document_manager),
):
    """ドキュメントの使用可否を設定"""
    success = await document_manager.set_document_enabled(filename, enable)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {filename} not found")
    return {"message": f"Document {filename} {'enabled' if enable else 'disabled'} successfully"}
