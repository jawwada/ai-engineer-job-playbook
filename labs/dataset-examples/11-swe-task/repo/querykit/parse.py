"""Query-string parsing."""
from urllib.parse import unquote_plus


def parse_query(qs):
    """Parse 'a=1&b=two' into {'a': '1', 'b': 'two'}."""
    result = {}
    if not qs:
        return result
    for pair in qs.split("&"):
        if not pair:
            continue
        key, _, value = pair.partition("=")
        result[unquote_plus(key)] = unquote_plus(value)
    return result
