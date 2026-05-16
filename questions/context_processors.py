from django.core.cache import cache

from .tasks import (
    BEST_MEMBERS_CACHE_KEY,
    POPULAR_TAGS_CACHE_KEY,
    update_best_members_cache,
    update_popular_tags_cache,
)


def sidebar_data(request):
    try:
        popular_tags = cache.get(POPULAR_TAGS_CACHE_KEY)
    except Exception:
        popular_tags = None
    if popular_tags is None:
        popular_tags = update_popular_tags_cache()

    try:
        best_members = cache.get(BEST_MEMBERS_CACHE_KEY)
    except Exception:
        best_members = None
    if best_members is None:
        best_members = update_best_members_cache()

    return {
        'popular_tags': popular_tags or [],
        'best_members': best_members or [],
    }
