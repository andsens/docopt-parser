from typing import Iterable, List

from docopt_parser import base


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
