from typing import List

from docopt_parser import base

class Sequence(base.AstNode):
  def __init__(self, items: List[base.AstLeaf]):
    _items: List[base.AstLeaf] = []
    for item in items:
      # Flatten the list
      if isinstance(item, Sequence):
        _items += item.items
      else:
        _items.append(item)
    super().__init__(_items)

  def __repr__(self) -> str:
    return f'''<Sequence>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'sequence'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]
