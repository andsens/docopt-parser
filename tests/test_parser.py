from tests.lang import DocoptAst as TestingAst
from docopt_parser.parser import DocoptAst as ParserAst
import unittest
from hypothesis import given


class TestParser(unittest.TestCase):
  @given(TestingAst.asts)
  def test_parse(self, s):
    assert isinstance(ParserAst.parse(str(s)), ParserAst)


  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
