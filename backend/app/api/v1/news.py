from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus
from app.core.exceptions import NotFoundException
from app.core.response import success_response
from app.db.models.business import NewsFetchRecord
from app.db.models.rbac import User
from app.schemas.news import NewsGenerateRequest, NewsProcessRequest, NewsSourceCreate, NewsSourceUpdate
from app.services.audit_service import record_operation_log
from app.services.news_service import (
    create_news_source as create_news_source_service,
    get_news,
    get_news_detail,
    get_news_source,
    list_news,
    list_news_fetch_records,
    list_news_sources,
    serialize_news,
    serialize_news_fetch_record,
    serialize_news_source,
    update_news_source as update_news_source_service,
)
from app.services.task_service import (
    dispatch_news_content_generation_task,
    dispatch_news_content_processing_task,
    dispatch_news_source_sync_task,
)

router = APIRouter()


@router.get("/sources")
def list_sources(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    source_type: NewsSourceType | None = None,
    is_enabled: bool | None = None,
    _: User = Depends(require_permission("news:source:list")),
    db: Session = Depends(get_db),
):
    items, total = list_news_sources(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        source_type=source_type,
        is_enabled=is_enabled,
    )
    return success_response(
        {
            "items": [serialize_news_source(item) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/sources/{source_id}")
def get_source_detail(
    source_id: int,
    _: User = Depends(require_permission("news:source:list")),
    db: Session = Depends(get_db),
):
    source = get_news_source(db, source_id)
    return success_response(serialize_news_source(source))


@router.post("/sources")
def create_source(
    payload: NewsSourceCreate,
    request: Request,
    current_user: User = Depends(require_permission("news:source:create")),
    db: Session = Depends(get_db),
):
    source = create_news_source_service(db, payload)
    record_operation_log(
        module="news_source",
        action="create",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news_source",
        biz_id=str(source.id),
        message=f"创建新闻源 {source.name}",
    )
    return success_response(serialize_news_source(source), status_code=201)


@router.put("/sources/{source_id}")
def update_source(
    source_id: int,
    payload: NewsSourceUpdate,
    request: Request,
    current_user: User = Depends(require_permission("news:source:update")),
    db: Session = Depends(get_db),
):
    source = update_news_source_service(db, source_id, payload)
    record_operation_log(
        module="news_source",
        action="update",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news_source",
        biz_id=str(source.id),
        message=f"更新新闻源 {source.name}",
    )
    return success_response(serialize_news_source(source))


@router.post("/sources/{source_id}/sync")
def sync_source(
    source_id: int,
    request: Request,
    current_user: User = Depends(require_permission("news:source:sync")),
    db: Session = Depends(get_db),
):
    source = get_news_source(db, source_id)
    task_job = dispatch_news_source_sync_task(
        db=db,
        news_source_id=source.id,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
        fetch_mode=NewsFetchMode.MANUAL.value,
    )
    record_operation_log(
        module="news_source",
        action="sync",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news_source",
        biz_id=str(source.id),
        message=f"手动同步新闻源 {source.name}",
    )
    return success_response(task_job, status_code=202)


@router.get("/records")
def list_fetch_records(
    page: int = 1,
    page_size: int = 20,
    source_id: int | None = None,
    status: str | None = None,
    _: User = Depends(require_permission("news:fetch-record:list")),
    db: Session = Depends(get_db),
):
    records, total = list_news_fetch_records(
        db,
        page=page,
        page_size=page_size,
        source_id=source_id,
        status=status,
    )
    return success_response(
        {
            "items": [serialize_news_fetch_record(record, source_name=source_name) for record, source_name in records],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/records/{record_id}")
def get_fetch_record_detail(
    record_id: int,
    _: User = Depends(require_permission("news:fetch-record:list")),
    db: Session = Depends(get_db),
):
    record = db.get(NewsFetchRecord, record_id)
    if record is None:
        raise NotFoundException(message="抓取记录不存在")
    source_name = None
    if record.source_id:
        source = get_news_source(db, record.source_id)
        source_name = source.name
    return success_response(serialize_news_fetch_record(record, source_name=source_name))


@router.get("")
def list_news_items(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: NewsStatus | None = None,
    source_id: int | None = None,
    category: str | None = None,
    _: User = Depends(require_permission("news:list")),
    db: Session = Depends(get_db),
):
    items, total = list_news(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        source_id=source_id,
        category=category,
    )
    return success_response(
        {
            "items": [serialize_news(item, brief=True) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/{news_id}")
def get_news_detail_view(
    news_id: int,
    _: User = Depends(require_permission("news:list")),
    db: Session = Depends(get_db),
):
    return success_response(get_news_detail(db, news_id))


@router.post("/{news_id}/generate")
def generate_news(
    news_id: int,
    request: Request,
    payload: NewsGenerateRequest | None = None,
    current_user: User = Depends(require_permission("news:generate")),
    db: Session = Depends(get_db),
):
    news = get_news(db, news_id)
    payload = payload or NewsGenerateRequest()
    task_job = dispatch_news_content_generation_task(
        db=db,
        news_id=news.id,
        style=payload.style,
        regenerate=payload.regenerate,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
    )
    record_operation_log(
        module="news",
        action="generate",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news",
        biz_id=str(news.id),
        message=f"触发新闻内容生成 {news.id}",
    )
    return success_response(task_job, status_code=202)


@router.post("/{news_id}/process")
def process_news(
    news_id: int,
    request: Request,
    payload: NewsProcessRequest | None = None,
    current_user: User = Depends(require_permission("news:process")),
    db: Session = Depends(get_db),
):
    news = get_news(db, news_id)
    payload = payload or NewsProcessRequest()
    task_job = dispatch_news_content_processing_task(
        db=db,
        news_id=news.id,
        style=payload.style,
        force=payload.force,
        triggered_by=current_user.id,
        request_id=request.state.request_id,
    )
    record_operation_log(
        module="news",
        action="process",
        operator_id=current_user.id,
        operator_name=current_user.username,
        request=request,
        biz_type="news",
        biz_id=str(news.id),
        message=f"触发新闻内容处理 {news.id}",
    )
    return success_response(task_job, status_code=202)
