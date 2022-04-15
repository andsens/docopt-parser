import pytest
from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser import base, parse, doc
import unittest
from hypothesis import given, settings  # type: ignore
import re


class TestParser(unittest.TestCase):
  @pytest.mark.filterwarnings('ignore:(.|\n)*this option is not referenced from the usage section.')
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, text: str):
    assert isinstance(parse(str(text))[0], base.AstLeaf)

  # TODO: Never expect <None> or <nl>


def test_unused_options():
  with pytest.warns(UserWarning, match=re.escape('<--- this option is not referenced from the usage section.')):
    parse('''Usage:
  prog cmd

Options:
  -f
''')

def test_duplicate_options():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('-f has already been specified on line 5')):
    parse('''Usage:
  prog cmd

Options:
  -f
  -f
''')

if __name__ == "__main__":
  unittest.main()
