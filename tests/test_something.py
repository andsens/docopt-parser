from hypothesis import given
from hypothesis.strategies import text


@given(text())
def test_defaults_match(s):
    assert decode(encode(s)) == s
