# querykit

Tiny helpers for URL query strings.

`parse_query("a=1&b=two")` returns `{"a": "1", "b": "two"}`. Keys and values are
percent-decoded and `+` becomes a space. A key that appears more than once maps to a list
of its values, in order.
