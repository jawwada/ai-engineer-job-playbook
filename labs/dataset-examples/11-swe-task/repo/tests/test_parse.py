from querykit import parse_query


def test_simple_pairs():
    assert parse_query("a=1&b=two") == {"a": "1", "b": "two"}


def test_empty_string():
    assert parse_query("") == {}


def test_plus_and_percent_decoding():
    assert parse_query("name=Ada+Lovelace&city=S%C3%A3o+Paulo") == {"name": "Ada Lovelace", "city": "São Paulo"}
