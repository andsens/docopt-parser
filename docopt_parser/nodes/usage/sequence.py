from ..astnode import AstNode
from parsec import optional, generate, eof
from .. import lookahead, either, whitespaces, nl

def seq(options):
  from .atom import atom

  @generate('sequence')
  def p():
    nodes = []
    while True:
      nodes.extend((yield atom(options)))
      if (yield optional(whitespaces)) is None:
        break
      if (yield lookahead(optional(either | nl | eof()))) is not None:
        break
    if len(nodes) > 1:
      return Sequence(nodes)
    else:
      return nodes[0]
  return p


class Sequence(AstNode):
  def __init__(self, items):
    self.items = items
    if len(items) > 1:
      new_items = []
      for item in items:
        if isinstance(item, Sequence):
          new_items += item.items
        else:
          new_items.append(item)
      self.items = new_items
    else:
      self.items = items

  def __repr__(self):
    return f'''<Sequence>
{self.indent(self.items)}'''
