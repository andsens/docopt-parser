from .astnode import AstNode
from parsec import generate
from . import char
from .choice import expr
from .sequence import Sequence

def optional(options):
  @generate('[optional]')
  def p():
    node = yield (char('[') >> expr(options) << char(']'))
    # Unnest [[optional]], or [sequence]
    if isinstance(node, (Optional, Sequence)):
      return Optional(node.items)
    elif node is None:
      return None
    else:
      return Optional([node])
  return p

class Optional(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f'''<Optional>
{self.indent(self.items)}'''
