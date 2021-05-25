from parsec import generate, optional
from .. import either, whitespaces
from ..astnode import AstNode


def expr(options):
  from .sequence import seq

  @generate('expression')
  def p():
    nodes = []
    while True:
      sequence = yield seq(options)
      if sequence is not None:
        nodes.append(sequence)
      if (yield optional(either << whitespaces)) is None:
        break
    if len(nodes) > 1:
      return Choice(nodes)
    else:
      return nodes[0] if len(nodes) else None
  return p


class Choice(AstNode):
  def __init__(self, items):
    if len(items) > 1:
      new_items = []
      for item in items:
        if isinstance(item, Choice):
          new_items += item.items
        else:
          new_items.append(item)
      self.items = new_items
    else:
      self.items = items

  def __repr__(self):
    return f'''<Choice>
{self.indent(self.items)}'''
