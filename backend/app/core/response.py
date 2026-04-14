from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.logging import get_request_id


def success_response(
    data: dict | list | str | int | None = None,
    message: str = "ok",
    status_code: int = 200,
) -> JSONResponse:
    payload = {
        "code": 0,
        "message": message,
        "data": jsonable_encoder(data if data is not None else {}),
        "request_id": get_request_id(),
    }
    return JSONResponse(status_code=status_code, content=payload)


def error_response(
    *,
    code: int,
    message: str,
    status_code: int,
    data: dict | None = None,
) -> JSONResponse:
    payload = {
        "code": code,
        "message": message,
        "data": jsonable_encoder(data or {}),
        "request_id": get_request_id(),
    }
    return JSONResponse(status_code=status_code, content=payload)
