from settings import redis


def pause_redis(seconds: int) -> None:
    """Pause redis processes"""
    timeout = seconds * 1000
    redis.client_pause(timeout=timeout, all=False)


def unpause_redis() -> None:
    """Resume redis processes that were previously paused"""
    redis.client_unpause()
