from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.simple_tag
def paginator_range(page_obj, delta=2):
    """Возвращает список номеров страниц с None вместо пропусков."""
    current = page_obj.number
    total = page_obj.paginator.num_pages

    pages = set()
    pages.update(range(1, min(3, total + 1)))
    pages.update(range(max(1, total - 1), total + 1))
    pages.update(range(max(1, current - delta), min(total, current + delta) + 1))

    result = []
    prev = None
    for p in sorted(pages):
        if prev is not None and p - prev > 1:
            result.append(None)
        result.append(p)
        prev = p
    return result
