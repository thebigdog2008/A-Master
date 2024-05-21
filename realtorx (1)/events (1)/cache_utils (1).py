from django.core.cache import cache


def get_events_cache_key(user_id, event_type):
    cache_key = "event_{user_id}_{event_type}".format(
        user_id=user_id, event_type=event_type
    )
    print("Getting event cache key ))))))))))))", cache_key)
    return cache_key


def decr(key, delta=1):
    print("DECR CALLED -------")
    cache_value = cache.get(key)
    print("cache_value -------", cache_value, delta)

    if cache_value is None:
        print("INSIDE VALUE ERROR")
        raise ValueError

    if cache_value - delta < 0:
        print("INSIDE if")
        cache.set(key, 0, timeout=None)
    else:
        cache.decr(key, delta=delta)
    print("------------> get ", cache.get(key))
