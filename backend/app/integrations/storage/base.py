from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class StoredObject:
    storage_path: str
    url: str
    bucket_name: str | None = None


class StorageClient(Protocol):
    def save_bytes(self, *, content: bytes, destination: str) -> StoredObject: ...

