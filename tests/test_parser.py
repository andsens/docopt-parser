from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser.nodes.docoptast import DocoptAst as ParserAst
import unittest
from hypothesis import given, settings


class TestParser(unittest.TestCase):
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, s):
    assert isinstance(ParserAst.parse(str(s)), ParserAst)


  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
