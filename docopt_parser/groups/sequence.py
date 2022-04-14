from typing import List
from parsec import optional, generate, eof, lookahead

from docopt_parser import base, elements, groups, parsers
from docopt_parser.helpers import GeneratorParser

@generate('sequence')
def sequence() -> GeneratorParser[base.AstLeaf | None]:
  Atom = base.AstLeaf | groups.Optional | elements.OptionsShortcut | elements.ArgumentSeparator | \
    List[elements.Short] | List[elements.Long] | elements.Argument | elements.Command | None
  atoms = (
    groups.group | groups.optional
    | elements.options_shortcut | elements.arg_separator | groups.option_list
    | elements.argument | elements.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')

  nodes: List[base.AstLeaf] = []
  while True:
    atom: Atom = yield atoms
    if isinstance(atom, list):
      # We're dealing with an optionlist, append all children to the sequence
      nodes.extend(atom)
    else:
      if atom is not None:
        nodes.append(atom)
    ws = yield parsers.whitespaces
    multi = yield optional(parsers.repeatable)
    if multi == '...':
      nodes[-1].repeatable = True
      ws = yield parsers.whitespaces
    if ws is None:
      break
    if (yield lookahead(optional(parsers.either | parsers.nl | eof()))) is not None:
      break
  if len(nodes) > 1:
    return Sequence(nodes)
  elif len(nodes) == 1:
    return nodes[0]
  else:
    return None


class Sequence(base.AstNode):
  def __init__(self, items: List[base.AstLeaf]):
    _items: List[base.AstLeaf] = []
    for item in items:
      # Flatten the list
      if isinstance(item, Sequence):
        _items += item.items
      else:
        _items.append(item)
    super().__init__(_items)

  def __repr__(self) -> str:
    return f'''<Sequence>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'sequence'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]
