import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.features.knowledge.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.features.knowledge.models import Document, DocumentStatus
from app.features.knowledge.processing.chunker import ChunkingStrategy, get_chunker
from app.features.knowledge.processing.embeddings import get_embedding_provider
from app.features.knowledge.processing.extractors import (
    SUPPORTED_MIME_TYPES,
    text_extractor,
)
from app.features.knowledge.processing.storage import (
    BaseStorageProvider,
    LocalStorageProvider,
)
from app.features.knowledge.processing.vector_store import get_document_vector_provider
from app.features.knowledge.repositories import DocumentRepository

logger = logging.getLogger("app.knowledge.services")

# Default providers
_storage_provider: BaseStorageProvider = LocalStorageProvider()


class KnowledgeService:
    """
    Service layer orchestrating document management, storage, chunking, embedding, retrieval, and reindexing.
    """

    @classmethod
    def get_storage_provider(cls) -> BaseStorageProvider:
        return _storage_provider

    @classmethod
    def set_storage_provider(cls, provider: BaseStorageProvider) -> None:
        global _storage_provider
        _storage_provider = provider

    # -------------------------------------------------------------------------
    # Upload and Management
    # -------------------------------------------------------------------------

    @classmethod
    async def upload_document(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        file: UploadFile,
    ) -> Document:
        # Validate MIME type
        mime_type = file.content_type or ""
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise UnsupportedFileTypeError(
                f"File type '{mime_type}' is not supported. "
                f"Accepted types: PDF, DOCX, TXT, Markdown."
            )

        # Validate file size
        file_bytes = await file.read()
        max_bytes = settings.KNOWLEDGE_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise FileTooLargeError(
                f"File size {len(file_bytes) // (1024 * 1024)}MB exceeds "
                f"maximum of {settings.KNOWLEDGE_MAX_FILE_SIZE_MB}MB."
            )

        # Generate storage identifier and persist file
        doc_id = uuid.uuid4()
        ext = Path(file.filename or "").suffix or ".bin"
        storage_filename = f"{doc_id}{ext}"

        storage = cls.get_storage_provider()
        storage.save_file(storage_filename, file_bytes)

        # Create Database Record
        doc_data = {
            "id": doc_id,
            "user_id": user_id,
            "original_filename": file.filename or storage_filename,
            "storage_filename": storage_filename,
            "mime_type": mime_type,
            "file_size": len(file_bytes),
            "status": DocumentStatus.UPLOADED,
            "retry_count": 0,
            "retries_exhausted": False,
            "metadata_json": {},
        }
        doc = await DocumentRepository.create(db, doc_data)
        await db.commit()

        logger.info(f"Document registered successfully: id={doc.id}, user_id={user_id}")
        return doc

    @classmethod
    async def get_document(
        cls, db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document:
        doc = await DocumentRepository.get_by_id_and_user(db, doc_id, user_id)
        if not doc:
            raise DocumentNotFoundError()
        return doc

    @classmethod
    async def list_documents(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> list[Document]:
        return await DocumentRepository.list_by_user(db, user_id)

    @classmethod
    async def get_status(
        cls, db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document:
        return await cls.get_document(db, doc_id, user_id)

    @classmethod
    async def delete_document(
        cls, db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        doc = await cls.get_document(db, doc_id, user_id)

        # Remove vector chunks
        try:
            vec_provider = get_document_vector_provider()
            # To delete all document chunks, we can reconstruct the index or perform deletion
            # For FAISS, we delete chunks by passing item_id (which maps to parent doc)
            # or deleting chunks individually if they are stored in metadata.
            # In our vector_provider.delete logic, it handles deletion of the matching item_id.
            # So we will trigger deletion.
            vec_provider.delete(user_id, doc_id)
        except Exception as e:
            logger.warning(f"Error removing vectors for doc {doc_id}: {e}")

        # Remove storage file
        try:
            storage = cls.get_storage_provider()
            storage.delete_file(doc.storage_filename)
        except Exception as e:
            logger.warning(f"Error deleting physical file for doc {doc_id}: {e}")

        # Remove database record
        await DocumentRepository.delete(db, doc_id)
        await db.commit()
        logger.info(f"Document {doc_id} permanently deleted.")

    # -------------------------------------------------------------------------
    # Background Processing Pipeline
    # -------------------------------------------------------------------------

    @classmethod
    async def process_document_background(cls, doc_id: uuid.UUID) -> None:
        logger.info(f"Background processing triggered for doc {doc_id}")
        async with SessionLocal() as db:
            doc = await DocumentRepository.get_by_id(db, doc_id)
            if not doc:
                logger.error(f"Document {doc_id} not found for background processing.")
                return

            await DocumentRepository.mark_processing(db, doc_id)
            await db.commit()

            # Create a temporary local file to extract text from (since extractors take Path)
            temp_dir = Path("./storage/tmp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / doc.storage_filename

            try:
                storage = cls.get_storage_provider()
                file_bytes = storage.load_file(doc.storage_filename)
                temp_path.write_bytes(file_bytes)

                # Text & Metadata Extraction
                text, metadata = text_extractor.extract_with_metadata(
                    temp_path, doc.mime_type
                )

                # Cleanup temp file
                if temp_path.exists():
                    temp_path.unlink()

                # Chunking strategy configuration
                strategy_str = getattr(
                    settings, "KNOWLEDGE_CHUNK_STRATEGY", "recursive"
                )
                try:
                    strategy = ChunkingStrategy(strategy_str)
                except ValueError:
                    strategy = ChunkingStrategy.RECURSIVE

                chunk_size = getattr(settings, "KNOWLEDGE_CHUNK_SIZE", 512)
                chunk_overlap = getattr(settings, "KNOWLEDGE_CHUNK_OVERLAP", 64)

                chunker = get_chunker(strategy, chunk_size, chunk_overlap)
                chunks = chunker.chunk(text)
                logger.info(f"Chunked doc {doc_id} into {len(chunks)} fragments.")

                # Generate Embeddings
                emb_provider = get_embedding_provider()
                embeddings = emb_provider.batch_embedding(chunks)

                # Push chunks to Vector Database
                vec_provider = get_document_vector_provider()
                # For FAISSVectorProvider, we add vectors representing each chunk.
                # To delete all document chunks cleanly on updates/deletion,
                # we key them to a combined item_id or pass them.
                # Since vec_provider.delete removes matching item_id, we can add
                # each chunk mapped to doc_id (parent document) if the provider supports mapping,
                # or create a composite UUID.
                # Let's map each chunk to doc_id so that calling `delete(user_id, doc_id)` removes them all!
                # Wait, our FAISSVectorProvider.add deletes existing matching item_id.
                # If we call add multiple times for the same item_id, it will only keep the last one!
                # To support multiple vectors for a single parent document, we can use a composite UUID,
                # and when deleting, we rebuild the FAISS index by filtering out metadata matching document_id.
                # Let's verify: in FAISSVectorProvider.delete:
                # `keep_indices = [i for i, m in enumerate(metadata_list) if m.get("item_id") != item_id_str]`
                # So if we set item_id to a chunk UUID and metadata to {"document_id": str(doc_id), ...},
                # we need to be able to delete all chunks matching the document_id.
                # Let's check how FAISSVectorProvider.delete is defined:
                # It deletes by matching item_id.
                # To support deleting all document chunks, we can override or implement delete inside
                # DocumentFAISSVectorProvider to delete all items matching "document_id" in metadata!
                # Yes! This is a brilliant design choice! Let's implement this custom delete in DocumentFAISSVectorProvider!
                # Let's double check if we can do this.
                # Yes! In DocumentFAISSVectorProvider, we override delete to filter out metadata where `metadata.get("document_id") == str(item_id)`.
                # So when we call `delete(user_id, doc_id)`, it filters out all vector chunks of that document!
                # This is completely seamless! Let's make sure we update DocumentFAISSVectorProvider.

                for i, (chunk_text, embedding) in enumerate(
                    zip(chunks, embeddings, strict=False)
                ):
                    chunk_id = uuid.uuid4()
                    chunk_metadata = {
                        "document_id": str(doc_id),
                        "chunk_index": i,
                        "text": chunk_text,
                        "category": metadata.get("title", ""),
                    }
                    vec_provider.add(doc.user_id, chunk_id, embedding, chunk_metadata)

                # Save final metadata and mark READY
                metadata["word_count"] = len(text.split())
                metadata["character_count"] = len(text)
                await DocumentRepository.mark_ready(db, doc_id, len(chunks), metadata)
                await db.commit()
                logger.info(f"Successfully processed and indexed document {doc_id}")

            except Exception as e:
                logger.exception(f"Fatal error processing document {doc_id}: {e}")
                if temp_path.exists():
                    temp_path.unlink()

                # Increment retry count
                retry_count = doc.retry_count + 1
                exhausted = retry_count >= 3
                update_vals = {
                    "retry_count": retry_count,
                    "retries_exhausted": exhausted,
                    "status": DocumentStatus.FAILED,
                    "error_message": str(e),
                    "processed_at": datetime.now(UTC),
                }
                await DocumentRepository.update_document(db, doc_id, update_vals)
                await db.commit()

    # -------------------------------------------------------------------------
    # Retrieval Pipeline
    # -------------------------------------------------------------------------

    @classmethod
    async def search_documents(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.5,
        category: str | None = None,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        # Embed query text
        emb_provider = get_embedding_provider()
        query_vector = emb_provider.generate_embedding(query)

        # Call vector provider search
        vec_provider = get_document_vector_provider()
        vec_results = vec_provider.search(
            user_id=user_id,
            embedding=query_vector,
            k=50,  # pull more candidate chunks for filtering
            threshold=similarity_threshold,
        )

        results = []
        for res in vec_results:
            meta = res.get("metadata", {})
            doc_id_str = meta.get("document_id")
            if not doc_id_str:
                continue

            # Filtering category (e.g. title metadata matches category, or similar)
            if category:
                doc_cat = meta.get("category", "")
                if category.strip().lower() not in doc_cat.lower():
                    continue

            # Metadata custom filters
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append(
                {
                    "document_id": uuid.UUID(doc_id_str),
                    "chunk_text": meta.get("text", ""),
                    "score": res["score"],
                    "metadata": meta,
                }
            )

        # Sort and truncate
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]

        # Hybrid retrieval placeholder:
        # e.g., run secondary SQL query over documents matching query keywords,
        # combine scores from TF-IDF/BM25 and vector search.
        results = cls._hybrid_retrieval_placeholder(results, query)

        # Reranking placeholder:
        # e.g., run cross-encoder / reranker model to re-score similarity of chunk_text.
        results = cls._reranking_placeholder(results, query)

        return results

    @classmethod
    def _hybrid_retrieval_placeholder(
        cls, results: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """
        Placeholder logic for future BM25/TF-IDF hybrid combination.
        """
        logger.debug(f"Hybrid retrieval placeholder triggered for query: {query}")
        return results

    @classmethod
    def _reranking_placeholder(
        cls, results: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """
        Placeholder logic for future cross-encoder reranking.
        """
        logger.debug(f"Reranking placeholder triggered for query: {query}")
        return results

    # -------------------------------------------------------------------------
    # Reindexing, Retry and Cleanup
    # -------------------------------------------------------------------------

    @classmethod
    async def reindex_user_documents(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Reindex all documents owned by user.
        """
        docs = await DocumentRepository.list_by_user(db, user_id)
        reindexed_count = 0
        for doc in docs:
            # Set back to UPLOADED and retry background processing
            update_vals = {
                "status": DocumentStatus.UPLOADED,
                "retry_count": 0,
                "retries_exhausted": False,
                "error_message": None,
            }
            await DocumentRepository.update_document(db, doc.id, update_vals)
            reindexed_count += 1

        await db.commit()
        return reindexed_count

    @classmethod
    async def retry_failed_documents(cls) -> int:
        """
        Background task to search for FAILED documents that have not exhausted retries.
        """
        logger.info("Background retry failed documents worker triggered")
        async with SessionLocal() as db:
            stmt = select(Document).where(
                and_(
                    Document.status == DocumentStatus.FAILED,
                    Document.retries_exhausted.is_(False),
                )
            )
            res = await db.execute(stmt)
            failed_docs = res.scalars().all()

            retried_count = 0
            for doc in failed_docs:
                update_vals = {
                    "status": DocumentStatus.UPLOADED,
                    "error_message": "Retrying processing...",
                }
                await DocumentRepository.update_document(db, doc.id, update_vals)
                retried_count += 1

            if retried_count > 0:
                await db.commit()
            return retried_count

    @classmethod
    async def cleanup_orphaned_files(cls) -> int:
        """
        Background task to clean up physical storage files that are not referenced in DB.
        """
        logger.info("Background storage cleanup worker triggered")
        async with SessionLocal() as db:
            stmt = select(Document.storage_filename)
            res = await db.execute(stmt)
            db_filenames = set(res.scalars().all())

        storage = cls.get_storage_provider()
        if hasattr(storage, "base_dir"):
            upload_dir = Path(storage.base_dir)
        else:
            upload_dir = Path(settings.KNOWLEDGE_UPLOAD_DIR)

        if not upload_dir.exists():
            return 0

        cleaned_count = 0
        for entry in upload_dir.iterdir():
            if entry.is_file() and not entry.name.startswith("."):
                if entry.name not in db_filenames:
                    try:
                        entry.unlink()
                        logger.info(f"Cleaned up orphaned storage file: {entry.name}")
                        cleaned_count += 1
                    except OSError as e:
                        logger.warning(
                            f"Failed to delete orphaned storage file {entry.name}: {e}"
                        )

        return cleaned_count
