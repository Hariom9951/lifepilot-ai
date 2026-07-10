import uuid
from pathlib import Path

import numpy as np

from app.core.config.settings import settings
from app.features.memory.vector_providers import BaseVectorProvider, FAISSVectorProvider


class DocumentFAISSVectorProvider(FAISSVectorProvider):
    """
    FAISS Vector Provider customized for knowledge documents.
    Stores indexes in a separate folder: <base_dir>/documents/<user_id>/.
    Supports batch deleting all chunks belonging to a document ID.
    """

    def _get_user_paths(self, user_id: uuid.UUID) -> tuple[Path, Path]:
        user_dir = self.base_dir / "documents" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / self.INDEX_FILENAME, user_dir / self.META_FILENAME

    def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        import faiss  # Lazy import

        index, metadata_list = self._load_index(user_id)
        item_id_str = str(item_id)

        # Filter out chunks matching item_id or having document_id set in metadata
        keep_indices = [
            i
            for i, m in enumerate(metadata_list)
            if m.get("item_id") != item_id_str
            and m.get("metadata", {}).get("document_id") != item_id_str
        ]
        if len(keep_indices) == len(metadata_list):
            return  # Not found

        new_index = faiss.IndexFlatL2(self.dimension)
        new_metadata = []

        if keep_indices:
            rem_vectors = []
            for idx in keep_indices:
                vec = index.reconstruct(idx)
                rem_vectors.append(vec)
                new_metadata.append(metadata_list[idx])

            new_index.add(np.array(rem_vectors, dtype=np.float32))

        self._save_index(user_id, new_index, new_metadata)


def get_document_vector_provider() -> BaseVectorProvider:
    """
    Factory helper to return the document-specific vector provider.
    """
    return DocumentFAISSVectorProvider(
        base_dir=Path(settings.KNOWLEDGE_VECTOR_DIR),
        dimension=384,
    )
