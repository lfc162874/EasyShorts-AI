class AppException(Exception):
    def __init__(
        self,
        *,
        message: str,
        code: int,
        status_code: int,
        data: dict | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "未认证或登录已失效") -> None:
        super().__init__(message=message, code=40100, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "无权限访问当前资源") -> None:
        super().__init__(message=message, code=40300, status_code=403)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message=message, code=40400, status_code=404)


class ConflictException(AppException):
    def __init__(self, message: str = "资源状态冲突") -> None:
        super().__init__(message=message, code=40900, status_code=409)


class ValidationException(AppException):
    def __init__(self, message: str = "业务校验失败", data: dict | None = None) -> None:
        super().__init__(message=message, code=42200, status_code=422, data=data)

