import pytest
from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser import doc, parse
import unittest
from hypothesis import given, settings  # type: ignore


class TestParser(unittest.TestCase):
  @pytest.mark.filterwarnings('ignore:(.|\n)*this option is not referenced from the usage section.')
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, text: str):
    assert isinstance(parse(str(text))[0], doc.Doc)

  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
