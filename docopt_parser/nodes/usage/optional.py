from ..astnode import AstNode
from parsec import generate
from .. import char
from .choice import expr
from .sequence import Sequence

class Optional(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f'''<Optional>
{self.indent(self.items)}'''

  def new(arg):
    return Optional(arg)

  def optional(options):
    @generate('[optional]')
    def p():
      node = yield (char('[') >> expr(options) << char(']'))
      if isinstance(node, (Optional, Sequence)):
        return Optional(node.items)
      else:
        return Optional([node])
    return p
