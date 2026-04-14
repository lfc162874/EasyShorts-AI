from pathlib import Path

from app.core.config import settings
from app.integrations.storage.base import StoredObject


class LocalStorageClient:
    def __init__(self) -> None:
        self.root = settings.local_storage_path
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, content: bytes, destination: str) -> StoredObject:
        target_path = self.root / destination
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        url = f"{settings.local_storage_public_prefix.rstrip('/')}/{destination}"
        return StoredObject(storage_path=destination, url=url)

