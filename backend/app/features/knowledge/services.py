"""
KnowledgeService — orchestrates document upload, background processing,
listing, status queries, and deletion.
"""

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.features.knowledge.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.features.knowledge.models import Document, DocumentStatus
from app.features.knowledge.processing.chunker import build_chunker_from_settings
from app.features.knowledge.processing.embeddings import get_embedding_service
from app.features.knowledge.processing.extractors import (
    SUPPORTED_MIME_TYPES,
    text_extractor,
)
from app.features.knowledge.processing.vector_store import get_vector_store
from app.features.knowledge.repositories import DocumentRepository

logger = logging.getLogger("app.knowledge.services")

# ---------------------------------------------------------------------------
# MIME type → file extension mapping (for safe storage filename)
# ---------------------------------------------------------------------------
_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/x-markdown": ".md",
}


def _get_upload_dir() -> Path:
    """Resolve and ensure the upload storage directory exists."""
    upload_dir = Path(settings.KNOWLEDGE_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _safe_storage_filename(
    original_filename: str, doc_id: uuid.UUID, mime_type: str
) -> str:
    """Generate a collision-safe storage filename from doc UUID."""
    ext = _MIME_TO_EXT.get(mime_type, ".bin")
    return f"{doc_id}{ext}"


class KnowledgeService:
    """
    Service layer implementing all business logic for the knowledge feature.
    Stateless: all dependencies are passed explicitly (dependency injection).
    """

    @staticmethod
    async def upload_document(
        db: AsyncSession,
        user_id: uuid.UUID,
        file: UploadFile,
    ) -> Document:
        """
        Validate, persist to disk, create DB record (status=UPLOADED).

        Args:
            db: Async database session.
            user_id: Authenticated user's UUID.
            file: Uploaded file from FastAPI.

        Returns:
            Created Document ORM instance.

        Raises:
            UnsupportedFileTypeError: If MIME type is not accepted.
            FileTooLargeError: If file exceeds configured size limit.
        """
        # 1. Validate MIME type
        mime_type = file.content_type or ""
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise UnsupportedFileTypeError(
                f"File type '{mime_type}' is not supported. "
                f"Accepted types: PDF, DOCX, TXT, Markdown."
            )

        # 2. Read file bytes and validate size
        file_bytes = await file.read()
        max_bytes = settings.KNOWLEDGE_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise FileTooLargeError(
                f"File size {len(file_bytes) // (1024 * 1024)}MB exceeds "
                f"maximum of {settings.KNOWLEDGE_MAX_FILE_SIZE_MB}MB."
            )

        # 3. Generate storage filename and persist bytes to disk
        doc_id = uuid.uuid4()
        storage_filename = _safe_storage_filename(
            file.filename or "upload", doc_id, mime_type
        )
        upload_dir = _get_upload_dir()
        file_path = upload_dir / storage_filename
        file_path.write_bytes(file_bytes)
        logger.info(f"Saved upload: {file_path} ({len(file_bytes)} bytes)")

        # 4. Create DB record
        document_data = {
            "id": doc_id,
            "user_id": user_id,
            "original_filename": file.filename or storage_filename,
            "storage_filename": storage_filename,
            "mime_type": mime_type,
            "file_size": len(file_bytes),
            "status": DocumentStatus.UPLOADED,
        }
        doc = await DocumentRepository.create(db, document_data)
        await db.commit()

        logger.info(
            f"Document record created: id={doc.id}, user={user_id}, "
            f"file={doc.original_filename}"
        )
        return doc

    @staticmethod
    async def process_document_background(doc_id: uuid.UUID) -> None:
        """
        Background task: extract → chunk → embed → store in FAISS.
        Creates its own DB session (cannot reuse the request session after response).

        Args:
            doc_id: UUID of the Document to process.
        """
        logger.info(f"Background processing started for doc {doc_id}.")

        async with SessionLocal() as db:
            try:
                # 1. Fetch document
                doc = await DocumentRepository.get_by_id(db, doc_id)
                if not doc:
                    logger.error(
                        f"Document {doc_id} not found during background processing."
                    )
                    return

                # 2. Mark as PROCESSING
                await DocumentRepository.mark_processing(db, doc_id)
                await db.commit()

                # 3. Resolve file path
                upload_dir = _get_upload_dir()
                file_path = upload_dir / doc.storage_filename

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Stored file missing: {doc.storage_filename}"
                    )

                # 4. Extract text
                raw_text = text_extractor.extract(file_path, doc.mime_type)
                if not raw_text.strip():
                    raise ValueError(
                        "Extracted text is empty — document may be corrupt."
                    )

                # 5. Chunk text
                chunker = build_chunker_from_settings()
                chunks = chunker.chunk(raw_text)
                logger.info(f"Doc {doc_id}: {len(chunks)} chunks created.")

                # 6. Embed chunks
                embedding_svc = get_embedding_service()
                embeddings = embedding_svc.embed(chunks)

                # 7. Store in FAISS
                vector_store = get_vector_store(doc.user_id)
                vector_store.add(doc_id, chunks, embeddings)

                # 8. Mark as READY
                await DocumentRepository.mark_ready(db, doc_id, chunk_count=len(chunks))
                await db.commit()

                logger.info(
                    f"Document {doc_id} processing complete ({len(chunks)} chunks)."
                )

            except Exception as exc:
                logger.exception(f"Document {doc_id} processing failed: {exc}")
                try:
                    await DocumentRepository.mark_failed(db, doc_id, str(exc))
                    await db.commit()
                except Exception as db_exc:
                    logger.error(
                        f"Could not update failed status for doc {doc_id}: {db_exc}"
                    )

    @staticmethod
    async def list_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
        """
        Return all documents owned by the requesting user.

        Args:
            db: Async database session.
            user_id: Authenticated user's UUID.
        """
        return await DocumentRepository.list_by_user(db, user_id)

    @staticmethod
    async def get_status(
        db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document:
        """
        Retrieve document status, enforcing ownership.

        Raises:
            DocumentNotFoundError: If doc does not exist or belongs to another user.
        """
        doc = await DocumentRepository.get_by_id_and_user(db, doc_id, user_id)
        if not doc:
            raise DocumentNotFoundError()
        return doc

    @staticmethod
    async def delete_document(
        db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """
        Delete document: FAISS vectors → disk file → DB record.

        Raises:
            DocumentNotFoundError: If doc does not exist or belongs to another user.
        """
        doc = await DocumentRepository.get_by_id_and_user(db, doc_id, user_id)
        if not doc:
            raise DocumentNotFoundError()

        # 1. Remove FAISS vectors (best-effort: do not fail if no vectors)
        try:
            vector_store = get_vector_store(user_id)
            vector_store.delete(doc_id)
        except Exception as exc:
            logger.warning(f"Could not remove FAISS vectors for doc {doc_id}: {exc}")

        # 2. Remove file from disk (best-effort)
        upload_dir = _get_upload_dir()
        file_path = upload_dir / doc.storage_filename
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except OSError as exc:
            logger.warning(f"Could not delete file {file_path}: {exc}")

        # 3. Remove DB record
        await DocumentRepository.delete(db, doc_id)
        await db.commit()
        logger.info(f"Document {doc_id} deleted by user {user_id}.")
