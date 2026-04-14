from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import FileCategory
from app.core.exceptions import ValidationException
from app.db.models.system import FileAsset
from app.integrations.storage.factory import get_storage_client


def _detect_category(content_type: str, extension: str) -> str:
    if content_type.startswith("image/") or extension in {".jpg", ".jpeg", ".png", ".webp"}:
        return FileCategory.IMAGE.value
    if content_type.startswith("audio/") or extension in {".mp3", ".wav", ".aac"}:
        return FileCategory.AUDIO.value
    if content_type.startswith("video/") or extension in {".mp4", ".mov", ".mkv"}:
        return FileCategory.VIDEO.value
    if extension in {".txt", ".pdf", ".doc", ".docx"}:
        return FileCategory.DOCUMENT.value
    return FileCategory.OTHER.value


async def save_upload_file(
    *,
    db: Session,
    upload_file: UploadFile,
    uploaded_by: int | None,
) -> FileAsset:
    original_name = upload_file.filename or "unnamed"
    extension = Path(original_name).suffix.lower()
    content_type = upload_file.content_type or "application/octet-stream"
    content = await upload_file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise ValidationException(message=f"上传文件不能超过 {settings.max_upload_size_mb} MB")

    category = _detect_category(content_type, extension)
    if category == FileCategory.OTHER.value:
        raise ValidationException(message="当前仅支持图片、音频、视频和文档类型文件上传")

    date_path = datetime.now(UTC).strftime("%Y/%m/%d")
    storage_name = f"{uuid4().hex}{extension}"
    relative_path = f"{date_path}/{storage_name}"

    stored = get_storage_client().save_bytes(content=content, destination=relative_path)
    file_asset = FileAsset(
        original_name=original_name,
        storage_name=storage_name,
        category=category,
        content_type=content_type,
        extension=extension,
        size=len(content),
        storage_backend=settings.storage_backend,
        storage_path=stored.storage_path,
        url=stored.url,
        bucket_name=stored.bucket_name,
        uploaded_by=uploaded_by,
    )
    db.add(file_asset)
    db.commit()
    db.refresh(file_asset)
    return file_asset

