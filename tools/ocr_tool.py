import pytesseract
from pdf2image import convert_from_path

from utils.logger import logger

# Batch size to avoid OOM on large scanned PDFs
OCR_BATCH_SIZE = 10


def ocr_pdf(pdf_path: str, dpi: int = 150) -> str:
    """
    OCR fallback for scanned/image-based PDFs.
    Processes pages in batches to avoid memory issues on large files.
    dpi=150 is a good balance of speed vs accuracy for hospital records.
    """
    logger.info(f"Running OCR on: {pdf_path} (dpi={dpi})")

    try:
        # Get total page count without loading all pages
        from pdf2image.pdf2image import pdfinfo_from_path
        try:
            info = pdfinfo_from_path(pdf_path)
            total_pages = info.get("Pages", 0)
        except Exception:
            total_pages = 999  # fallback: process until no more pages

        logger.info(f"OCR: total pages = {total_pages}")

        extracted_pages = []
        page_num = 1

        while page_num <= total_pages:
            last_page = min(page_num + OCR_BATCH_SIZE - 1, total_pages)
            logger.info(
                f"OCR batch: pages {page_num}-{last_page}"
            )

            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    first_page=page_num,
                    last_page=last_page,
                )
            except Exception as e:
                logger.warning(
                    f"Batch pages {page_num}-{last_page} failed: {e}"
                )
                page_num += OCR_BATCH_SIZE
                continue

            for i, image in enumerate(images):
                try:
                    text = pytesseract.image_to_string(image)
                    if text.strip():
                        extracted_pages.append(text)
                except Exception as pe:
                    logger.warning(
                        f"OCR page {page_num + i} failed: {pe}"
                    )

            page_num += OCR_BATCH_SIZE

        result = "\n\n".join(extracted_pages)
        logger.info(f"OCR complete: {len(result)} total characters")
        return result

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""
