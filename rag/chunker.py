from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str) -> list[str]:
    """
    Split extracted PDF text into overlapping chunks for RAG retrieval.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_text(text)
    return [c for c in chunks if c.strip()]
