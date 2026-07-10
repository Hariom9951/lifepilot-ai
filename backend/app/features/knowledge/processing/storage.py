import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config.settings import settings

logger = logging.getLogger("app.knowledge.storage")


class BaseStorageProvider(ABC):
    """
    Abstract Base Class for managing document storage.
    Enables swapping out local storage for AWS S3 or GCP Storage.
    """

    @abstractmethod
    def save_file(self, storage_name: str, content: bytes) -> str:
        """
        Save file to storage and return its resolved path/URI.
        """
        pass

    @abstractmethod
    def load_file(self, storage_name: str) -> bytes:
        """
        Load file content from storage.
        """
        pass

    @abstractmethod
    def delete_file(self, storage_name: str) -> None:
        """
        Delete file from storage.
        """
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Concrete storage provider persisting files to the local file system.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(settings.KNOWLEDGE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, storage_name: str) -> Path:
        return self.base_dir / storage_name

    def save_file(self, storage_name: str, content: bytes) -> str:
        file_path = self._resolve_path(storage_name)
        file_path.write_bytes(content)
        logger.info(f"Saved file to local storage: {file_path}")
        return str(file_path)

    def load_file(self, storage_name: str) -> bytes:
        file_path = self._resolve_path(storage_name)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found in local storage: {storage_name}")
        return file_path.read_bytes()

    def delete_file(self, storage_name: str) -> None:
        file_path = self._resolve_path(storage_name)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file from local storage: {file_path}")
        except OSError as e:
            logger.warning(f"Could not delete file from local storage: {e}")
