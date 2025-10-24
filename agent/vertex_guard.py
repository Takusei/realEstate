import time
from functools import lru_cache


# 10 min cache; simplest: LRU of last 256 queries
@lru_cache(maxsize=256)
def cached_parse(query: str) -> dict:
    from vertex_nlu import parse_query_to_filters_with_vertex

    return parse_query_to_filters_with_vertex(query)


# optional TTL wrapper
_CACHE = {}


def cached_ttl_parse(query: str, ttl_sec=600):
    now = time.time()
    hit = _CACHE.get(query)
    if hit and now - hit["t"] < ttl_sec:
        return hit["v"]
    from vertex_nlu import parse_query_to_filters_with_vertex

    v = parse_query_to_filters_with_vertex(query)
    _CACHE[query] = {"v": v, "t": now}
    return v
