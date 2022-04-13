from typing import Iterator, Union
from .option import Option
from .optional import Optional
from . import string

options_shortcut = string('options').desc('options shortcut').parsecmap(lambda s: OptionsShortcut())

class OptionsShortcut(Optional):
  options: list[Option]

  def __init__(self):
    self.options = []

  @property
  def items(self) -> list[Option]:
    return list(filter(lambda o: o.shortcut, self.options))

  def __repr__(self) -> str:
    return f'''<OptionsShortcut>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, list[dict]]]]:
    yield 'type', 'optionsshortcut'
    yield 'repeatable', self.repeatable
    yield 'items', list(map(dict, self.items))

  @property
  def multiple(self) -> bool:
    return all(map(lambda i: i.multiple, self.items))

  @multiple.setter
  def multiple(self, value: bool) -> None:
    for item in self.items:
      item.multiple = value
