from tests.lang import docopt_help, Usage
from docopt_parser import DocoptParseError
from docopt_parser.parser import DocoptAst
import unittest
from hypothesis import given


class TestParser(unittest.TestCase):
  @given(Usage.usages)
  def test_parse(self, s):
    assert isinstance(DocoptAst.parse(str(s)), DocoptAst)


  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
