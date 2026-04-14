from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger, set_request_id
from app.core.response import error_response
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.audit_service import record_error_log
from app.services.bootstrap_service import bootstrap_default_data

configure_logging()
logger = get_logger(__name__)
settings.local_storage_path.mkdir(parents=True, exist_ok=True)
if settings.sqlite_data_path is not None:
    settings.sqlite_data_path.parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.bootstrap_admin_on_startup:
        with SessionLocal() as db:
            bootstrap_default_data(db)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    settings.local_storage_public_prefix,
    StaticFiles(directory=settings.local_storage_path),
    name="assets",
)
app.include_router(api_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    request.state.request_id = request_id
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    record_error_log(
        request=request,
        error_code=exc.code,
        error_type=exc.__class__.__name__,
        error_message=exc.message,
    )
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        data=exc.data,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    record_error_log(
        request=request,
        error_code=42200,
        error_type="RequestValidationError",
        error_message="请求参数校验失败",
        exc=exc,
    )
    return error_response(
        code=42200,
        message="请求参数校验失败",
        status_code=422,
        data={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled exception")
    record_error_log(
        request=request,
        error_code=50000,
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        exc=exc,
    )
    return error_response(
        code=50000,
        message="系统内部错误",
        status_code=500,
    )
