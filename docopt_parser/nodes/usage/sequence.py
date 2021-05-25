from ..astnode import AstNode
from parsec import optional, generate, eof
from .. import lookahead, either, whitespaces, nl, multiple

def seq(options):
  from .group import group
  from .optional import optional as _optional
  from .optionsshortcut import options_shortcut
  from .argumentseparator import arg_separator
  from .optionlist import option_list
  from ..argument import argument
  from .command import command
  from .multiple import Multiple

  atoms = (
    group(options) | _optional(options)
    | options_shortcut(options) | option_list(options)
    | argument | command | arg_separator
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')

  @generate('sequence')
  def p():
    nodes = []
    while True:
      atom = yield atoms
      if isinstance(atom, list):
        # We're dealing with an optionlist or shortcut, append all children to the sequence
        nodes.extend(atom)
      else:
        if atom is not None:
          nodes.append(atom)
      ws = yield whitespaces
      multi = yield optional(multiple)
      if multi == '...':
        nodes[-1] = Multiple(nodes[-1])
        ws = yield whitespaces
      if ws is None:
        break
      if (yield lookahead(optional(either | nl | eof()))) is not None:
        break
    if len(nodes) > 1:
      return Sequence(nodes)
    else:
      return nodes[0] if len(nodes) else None
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
