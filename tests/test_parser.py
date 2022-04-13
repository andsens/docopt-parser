import pytest
from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser.nodes.astnode import AstLeaf
from docopt_parser import parse_strict
import unittest
from hypothesis import given, settings
import re


class TestParser(unittest.TestCase):
  @pytest.mark.filterwarnings(r'ignore:\d+ options are not referenced from the usage section:')
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, s):
    assert isinstance(parse_strict(str(s)), AstLeaf)

  # TODO: Never expect <None> or <nl>


def test_unused_options():
  with pytest.warns(UserWarning, match=re.escape('''2 options are not referenced from the usage section:
* --sdfsdf
* -k''')):
    parse_strict('''Usage:
  prog cmd [options]

Options:
  -f, --sdfsdf
  -k=ARG  Some arg
''')

if __name__ == "__main__":
  unittest.main()
