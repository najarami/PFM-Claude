from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_log_id: Optional[str]
    total_parsed: int
    inserted: int
    duplicates: int
    errors: list[str] = []
    bank_detected: Optional[str] = None
    parser_used: Optional[str] = None
