import fitz

from utils.logger import logger


def read_pdf(pdf_path: str) -> str:
    """
    Extract text from a digital (non-scanned) PDF using PyMuPDF.
    Returns empty string if no text is found (triggers OCR fallback).
    """
    try:
        logger.info(f"Reading PDF: {pdf_path}")
        document = fitz.open(pdf_path)
        pages = []

        for page in document:
            text = page.get_text()
            if text.strip():
                pages.append(text)

        result = "\n".join(pages)
        logger.info(f"PyMuPDF extracted {len(result)} characters")
        return result

    except Exception as e:
        logger.error(f"PDF read error: {e}")
        return ""
