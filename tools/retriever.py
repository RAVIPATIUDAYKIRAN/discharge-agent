from config import TOP_K
from utils.logger import logger


class Retriever:
    """
    Wraps FAISS similarity search.
    Falls back to returning the first N chunks if vector store is unavailable.
    """

    def __init__(self, vector_store, all_chunks: list[str] | None = None):
        self.vector_store = vector_store
        self.all_chunks = all_chunks or []

    def retrieve(self, query: str) -> list[str]:

        # Primary: FAISS similarity search
        if self.vector_store is not None:
            try:
                docs = self.vector_store.similarity_search(
                    query, k=TOP_K
                )
                return [doc.page_content for doc in docs]
            except Exception as e:
                logger.warning(
                    f"FAISS retrieval failed for query '{query[:50]}': {e}. "
                    "Falling back to sequential chunks."
                )

        # Fallback: return first TOP_K chunks sequentially
        logger.info(
            f"Using fallback retrieval for query: {query[:60]}"
        )
        return self.all_chunks[:TOP_K]
