import logging
import os

from config import LOG_FILE_PATH


def setup_logger():

    os.makedirs(
        os.path.dirname(LOG_FILE_PATH),
        exist_ok=True
    )

    logger = logging.getLogger("DischargeAgent")

    logger.setLevel(logging.INFO)

    if not logger.handlers:

        file_handler = logging.FileHandler(
            LOG_FILE_PATH,
            encoding="utf-8"
        )

        stream_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


logger = setup_logger()
