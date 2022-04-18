from tests.lang import DocoptAst as DocoptAstGenerator
from docopt_parser import base, groups, parse
import unittest
from hypothesis import given, settings


class TestParser(unittest.TestCase):
  @settings(max_examples=500)
  @given(DocoptAstGenerator.asts)
  def test_parse(self, text: str):
    usage = parse(str(text))

  # Make sure only Choice, Sequence, Optional, Repeatable and IdentNodes are in the ast
    def walk(node: base.Node):
      assert isinstance(node, (groups.Choice, groups.Sequence, groups.Optional, groups.Repeatable, base.Leaf))
      if isinstance(node, (base.Group)):
        for item in node.items:
          walk(item)
    walk(usage)
  # TODO: Choice should never have only one child unless it's the root
  # TODO: Sequence should never have only one child?
  # TODO: Repeatable should always only have one child
  # TODO: Never expect <None> or <nl>

if __name__ == "__main__":
  unittest.main()
