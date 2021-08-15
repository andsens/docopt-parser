from .astnode import AstNode
from parsec import optional, generate, eof
from . import lookahead, either, whitespaces, nl, repeatable

def seq(options):
  from .group import group
  from .optional import optional as _optional
  from .options_shortcut import options_shortcut
  from .argumentseparator import arg_separator
  from .optionlist import option_list
  from .argument import argument
  from .command import command

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
      multi = yield optional(repeatable)
      if multi == '...':
        nodes[-1].repeatable = True
        ws = yield whitespaces
      if ws is None:
        break
      if (yield lookahead(optional(either | nl | eof()))) is not None:
        break
    if len(nodes) > 1:
      return Sequence(nodes)
    elif len(nodes) == 1:
      return nodes[0]
    else:
      return None
  return p


class Sequence(AstNode):
  def __init__(self, items):
    _items = []
    for item in items:
      # Flatten the list
      if isinstance(item, Sequence):
        _items += item.items
      else:
        _items.append(item)
    super().__init__(_items)

  def __repr__(self):
    return f'''<Sequence>{self.repeatable_suffix}
{self.indent(self.items)}'''
