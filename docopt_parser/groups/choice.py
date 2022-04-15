from typing import Iterable, List
from parsec import generate, optional

from docopt_parser import base, parsers
from docopt_parser.base.astleaf import AstLeaf
from docopt_parser.helpers import GeneratorParser

@generate('expression')
def expr() -> GeneratorParser[AstLeaf | None]:
  from .sequence import sequence
  nodes: List[base.AstLeaf] = []
  while True:
    _sequence = yield sequence
    if _sequence is not None:
      nodes.append(_sequence)
    if (yield optional(parsers.either << parsers.whitespaces)) is None:
      break
  if len(nodes) > 1:
    return Choice(nodes)
  elif len(nodes) == 1:
    return nodes[0]
  else:
    return None


class Choice(base.AstNode):
  def __init__(self, items: Iterable[base.AstLeaf]):
    _items: List[base.AstLeaf] = []
    for item in items:
      # Flatten the list, "a | (b | c)" is the same as "a | b | c"
      if isinstance(item, Choice):
        _items += item.items
      else:
        _items.append(item)
    super().__init__(_items)

  def __repr__(self):
    return f'''<Choice>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'repeatable', self.repeatable
    yield 'type', 'choice'
    yield 'items', [dict(item) for item in self.items]
