from typing import Generator, Iterator, Union
from .astleaf import AstLeaf
from .astnode import AstNode
from parsec import Parser, generate
from . import char
from .choice import expr
from .sequence import Sequence

class Optional(AstNode):
  def __init__(self, items: AstLeaf):
    super().__init__(items)

  def __repr__(self):
    return f'''<Optional>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, list[dict]]]]:
    yield 'type', 'optional'
    yield 'repeatable', self.repeatable
    yield 'items', list(map(dict, self.items))

@generate('[optional]')
def optional() -> Generator[Parser, Parser, Union[Optional, None]]:
  node = yield (char('[') >> expr << char(']'))
  # Unnest [[optional]], or [sequence]
  if isinstance(node, (Optional, Sequence)):
    return Optional(node.items)
  elif node is None:
    return None
  else:
    return Optional([node])
