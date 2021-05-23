from ..astnode import AstNode
from parsec import optional, generate, eof
from .. import lookahead, either, whitespaces, nl

def seq(options):
  from .group import Group
  from .optional import Optional
  from .optionsshortcut import OptionsShortcut
  from .argumentseparator import ArgumentSeparator
  from .optionlist import OptionList
  from ..argument import Argument
  from .command import Command
  from .multiple import Multiple

  @generate('sequence')
  def p():
    nodes = []
    while True:
      atom = yield (
        Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
        | ArgumentSeparator.separator | OptionList.options(options)
        | Argument.arg | Command.command
      ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')
      if isinstance(atom, list):
        # We're dealing with an optionlist, append all children to the sequence
        # The "..." only affects the last option in the list
        atom[-1] = yield Multiple.multi(atom[-1])
        nodes.extend(atom)
      else:
        atom = yield Multiple.multi(atom)
        nodes.append(atom)
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
