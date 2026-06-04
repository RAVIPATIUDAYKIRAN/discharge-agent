from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from config import OPENAI_API_KEY
from utils.logger import logger


def create_vector_store(chunks: list[str]):
    """
    Build a FAISS vector store from text chunks using OpenAI embeddings.
    Returns None on failure so the agent can degrade gracefully.
    """
    if not chunks:
        logger.error("No chunks provided to create_vector_store.")
        return None

    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )
        store = FAISS.from_texts(texts=chunks, embedding=embeddings)
        logger.info(f"Vector store created with {len(chunks)} chunks.")
        return store

    except Exception as e:
        logger.error(f"Vector store creation failed: {e}")
        return None
