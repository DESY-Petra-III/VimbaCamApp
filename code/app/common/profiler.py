import time
import logging

__all__ = ["profile"]

def profile(func):
    def wrap(*args, **kwargs):
        started_at = time.time()
        result = func(*args, **kwargs)
        logging.debug("Func {} processing time ({} ms)".format(func, time.time() - started_at))
        return result

    return wrap