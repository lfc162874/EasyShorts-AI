from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.response import success_response
from app.db.models.rbac import User
from app.services.audit_service import record_operation_log
from app.services.upload_service import save_upload_file

router = APIRouter()


@router.post("/files")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("system:file:upload")),
    db: Session = Depends(get_db),
):
    asset = await save_upload_file(db=db, upload_file=file, uploaded_by=current_user.id)
    record_operation_log(
        module="file",
        action="upload",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="file_asset",
        biz_id=str(asset.id),
        message=f"上传文件 {asset.original_name}",
    )
    return success_response(asset, status_code=201)
