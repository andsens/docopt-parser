from parsec import generate, optional
from . import either, whitespaces
from .astnode import AstNode


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
    elif len(nodes) == 1:
      return nodes[0]
    else:
      return None
  return p


class Choice(AstNode):
  def __init__(self, items):
    self.items = []
    for item in items:
      # Flatten the list, "a | (b | c)" is the same as "a | b | c"
      if isinstance(item, Choice):
        self.items += item.items
      else:
        self.items.append(item)

  def __repr__(self):
    return f'''<Choice>{self.repeatable_suffix}
{self.indent(self.items)}'''
