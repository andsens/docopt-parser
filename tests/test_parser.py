import pytest
from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser import base, parse
import unittest
from hypothesis import given, settings
import re


class TestParser(unittest.TestCase):
  @pytest.mark.filterwarnings('ignore:(.|\n)*this option is not referenced from the usage section.')
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, s):
    assert isinstance(parse(str(s)), base.AstLeaf)

  # TODO: Never expect <None> or <nl>


def test_unused_options():
  with pytest.warns(UserWarning, match=re.escape('''<--- this option is not referenced from the usage section.''')):
    parse('''Usage:
  prog cmd [options]

Options:
  -f, --sdfsdf
  -k=ARG  Some arg
''')

if __name__ == "__main__":
  unittest.main()
