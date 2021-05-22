from ..astnode import AstNode
from parsec import optional, generate
from .. import exclude, either, whitespaces, eol

def seq(options):
  from .atom import atom

  @generate('sequence')
  def p():
    nodes = [(yield atom(options))]
    while (yield optional(exclude(whitespaces, whitespaces >> either ^ eol))) is not None:
      nodes.append((yield atom(options)))
      # TODO: whitespace consumption duplicated in usage.lin
      # if (yield optional(lookahead(eol))) is not None:
      #   yield optional(whitespaces)
      #   break
    # Consume any trailing whitespaces
    yield optional(whitespaces)
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
