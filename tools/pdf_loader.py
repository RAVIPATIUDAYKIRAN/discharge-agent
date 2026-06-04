import os

from tools.pdf_reader import read_pdf
from tools.ocr_tool import ocr_pdf
from utils.logger import logger

# Minimum character threshold to consider text extraction successful
MIN_TEXT_LENGTH = 100


def load_patient_pdf(pdf_path: str) -> str:
    """
    Smart PDF loader:
    1. Try PyMuPDF (fast, works for digital PDFs).
    2. If text is too short, fall back to OCR (for scanned PDFs).
    3. Raises ValueError if both fail.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Loading patient PDF: {pdf_path}")

    # Step 1: Try direct text extraction
    text = read_pdf(pdf_path)

    if len(text.strip()) >= MIN_TEXT_LENGTH:
        logger.info("Direct text extraction succeeded.")
        return text

    # Step 2: OCR fallback
    logger.info(
        f"Direct extraction returned only {len(text.strip())} chars. "
        "Falling back to OCR..."
    )

    text = ocr_pdf(pdf_path, dpi=200)

    if len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Could not extract text from PDF: {pdf_path}. "
            "Both direct extraction and OCR returned insufficient text."
        )

    logger.info(f"OCR fallback succeeded: {len(text)} chars extracted.")
    return text
