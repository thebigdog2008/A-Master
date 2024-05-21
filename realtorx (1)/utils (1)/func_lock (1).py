import functools
import logging
from hashlib import md5

from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_func_lock_id(name, args, kwargs):
    to_hash = str((args, tuple(sorted(kwargs.items())))).encode("utf-8")
    args_hash = md5(to_hash).hexdigest()
    lock_id = "{0}-function_cache_lock-{1}".format(name, args_hash)
    return lock_id


class FunctionLocked:
    """Dummy result to indicate execution was interrupted"""

    pass


locked = FunctionLocked()


def function_cache_lock(lock_expire=10 * 60):
    """
    Prevent function from being executed with same arguments during the lock
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = get_func_lock_id(func.__name__, args, kwargs)

            if not cache.add(lock_id, True, timeout=lock_expire):
                logger.warning(
                    "Blocked task duplicate '{0}'. Lock ID: {1}".format(
                        func.__name__,
                        lock_id,
                    )
                )

                return locked
            try:
                return func(*args, **kwargs)
            finally:
                cache.delete(lock_id)

        return wrapper

    return decorator
