from typing import Generator, Iterable, Iterator, Union
from parsec import Parser, generate, optional

from docopt_parser.nodes.astleaf import AstLeaf
from . import either, whitespaces
from .astnode import AstNode


@generate('expression')
def expr() -> Generator[Parser, Parser, Union[AstLeaf, None]]:
  from .sequence import seq
  nodes = []
  while True:
    sequence = yield seq
    if sequence is not None:
      nodes.append(sequence)
    if (yield optional(either << whitespaces)) is None:
      break
  if len(nodes) > 1:
    return Choice(nodes)
  elif len(nodes) == 1:
    return nodes[0]
  else:
    return None


class Choice(AstNode):
  def __init__(self, items: Iterable[AstLeaf]):
    _items = []
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

  def __iter__(self) -> Iterator[tuple[str, Union[bool, str, list[dict]]]]:
    yield 'repeatable', self.repeatable
    yield 'type', 'choice'
    yield 'items', list(map(dict, self.items))
