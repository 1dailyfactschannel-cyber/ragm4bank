import asyncio
import functools
from app.utils.logging import setup_logger

logger = setup_logger()


def async_retry(max_retries: int = 3, backoff_base: float = 1.0, exceptions=(Exception,)):
    """
    Декоратор для async функций с exponential backoff.
    
    Args:
        max_retries: максимальное количество попыток
        backoff_base: базовое время ожидания (удваивается каждую попытку)
        exceptions: кортеж исключений, которые перехватываются
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    wait_time = backoff_base * (2 ** (attempt - 1))
                    logger.warning(f"Function {func.__name__} attempt {attempt} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator
