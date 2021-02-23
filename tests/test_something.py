from tests.lang import docopt_help
from docopt_parser import DocoptParseError
from docopt_parser.parser import DocoptAst
import unittest
from hypothesis import given
from hypothesis.strategies import text


class TestParser(unittest.TestCase):
  @given(text())
  def test_parse_failure(self, s):
    with self.assertRaises(DocoptParseError):
      DocoptAst.parse(s)

  @given(docopt_help())
  def test_parse(self, s):
    assert isinstance(DocoptAst.parse(s), DocoptAst)

if __name__ == "__main__":
  unittest.main()
