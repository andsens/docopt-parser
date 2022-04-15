from typing import List
from parsec import generate

from docopt_parser import base, elements, groups, parsers
from docopt_parser.base.astleaf import AstLeaf
from docopt_parser.helpers import GeneratorParser

class Optional(base.AstNode):
  def __init__(self, items: List[base.AstLeaf]):
    super().__init__(items)

  def __repr__(self):
    return f'''<Optional>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'optional'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]

@generate('[optional]')
def optional() -> GeneratorParser[Optional | elements.OptionsShortcut | None]:
  node: AstLeaf = yield (parsers.char('[') >> groups.choice << parsers.char(']'))
  # Unnest [[optional]], or [options]
  if isinstance(node, (Optional, elements.OptionsShortcut)):
    return node
  elif node is None:
    return None
  else:
    return Optional([node])
