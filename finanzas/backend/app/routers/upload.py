from fastapi import APIRouter, Depends, File, Form, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.upload import UploadResponse
from app.services.upload_service import process_upload

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    result = await process_upload(
        filename=file.filename,
        content=content,
        account_id=account_id,
        session=session,
    )
    return UploadResponse(
        upload_log_id=result.upload_log_id,
        total_parsed=result.total_parsed,
        inserted=result.inserted,
        duplicates=result.duplicates,
        errors=result.errors,
    )
