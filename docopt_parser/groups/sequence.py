from typing import Generator, Iterator, Union
from parsec import Parser, optional, generate, eof

from docopt_parser import base, elements, groups, parsers

@generate('sequence')
def sequence() -> Generator[Parser, Parser, Union[base.AstLeaf, None]]:

  atoms = (
    groups.group | groups.optional
    | elements.options_shortcut | elements.arg_separator | groups.option_list
    | elements.argument | elements.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')

  nodes = []
  while True:
    atom = yield atoms
    if isinstance(atom, list):
      # We're dealing with an optionlist or shortcut, append all children to the sequence
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
    if (yield parsers.lookahead(optional(parsers.either | parsers.nl | eof()))) is not None:
      break
  if len(nodes) > 1:
    return Sequence(nodes)
  elif len(nodes) == 1:
    return nodes[0]
  else:
    return None


class Sequence(base.AstNode):
  def __init__(self, items: list[base.AstLeaf]):
    _items = []
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

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, list[dict]]]]:
    yield 'type', 'sequence'
    yield 'repeatable', self.repeatable
    yield 'items', list(map(dict, self.items))
