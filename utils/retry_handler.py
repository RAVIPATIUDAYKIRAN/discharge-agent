from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
)

from utils.logger import logger


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def execute_with_retry(func, *args, **kwargs):
    """
    Execute a function with up to 3 retries, 2s wait between attempts.
    Logs each attempt failure.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Retry attempt failed for {func.__name__}: {e}")
        raise
