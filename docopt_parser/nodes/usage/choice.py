from parsec import many, generate, optional
from .. import char
from ..astnode import AstNode


either = (many(char(' ')) >> char('|') << many(char(' '))).desc('<pipe> (|)')
def expr(options):
  from .sequence import seq

  @generate('expression')
  def p():
    nodes = [(yield seq(options))]
    while (yield optional(either)) is not None:
      nodes.append((yield seq(options)))
    if len(nodes) > 1:
      return Choice(nodes)
    else:
      return nodes[0]
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
