from app.core.config import settings
from app.integrations.storage.base import StorageClient
from app.integrations.storage.local import LocalStorageClient


def get_storage_client() -> StorageClient:
    if settings.storage_backend == "local":
        return LocalStorageClient()
    raise NotImplementedError(f"unsupported storage backend: {settings.storage_backend}")

