from .astnode import AstNode
from parsec import generate
from . import char
from .choice import expr
from .sequence import Sequence

@generate('[optional]')
def optional():
  node = yield (char('[') >> expr << char(']'))
  # Unnest [[optional]], or [sequence]
  if isinstance(node, (Optional, Sequence)):
    return Optional(node.items)
  elif node is None:
    return None
  else:
    return Optional([node])

class Optional(AstNode):
  def __init__(self, items):
    super().__init__(items)

  def __repr__(self):
    return f'''<Optional>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self):
    yield 'type', 'optional'
    yield 'repeatable', self.repeatable
    yield 'items', list(map(dict, self.items))
