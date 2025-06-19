import time
import logging
from typing import Callable

def retry(max_attempts=3, delay=1):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logging.warning(f"재시도 중... ({attempt + 1}/{max_attempts})")
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator
