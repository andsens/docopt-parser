from tests.lang import docopt_help
from docopt_parser import DocoptParseError
from docopt_parser.parser import DocoptAst
import unittest
from hypothesis import given


class TestParser(unittest.TestCase):
  @given(docopt_help())
  def test_parse(self, s):
    assert isinstance(DocoptAst.parse(s), DocoptAst)


  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
