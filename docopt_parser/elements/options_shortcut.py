
from typing import Iterable
from docopt_parser import base, elements, parsers, marked

options_shortcut = parsers.string('options').mark().desc('options shortcut').parsecmap(lambda n: OptionsShortcut(n))

class OptionsShortcut(base.AstNode):
  __name: marked.Marked[str]
  items: Iterable[elements.DocumentedOption]
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple[str]):
    super().__init__([])
    self.__name = marked.Marked(name)
    self.mark = marked.Mark(self.__name.start, self.__name.end)

  def __repr__(self) -> str:
    return f'''<OptionsShortcut>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'optionsshortcut'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]

  @property
  def multiple(self) -> bool:
    return all(map(lambda i: i.multiple, self.items))

  @multiple.setter
  def multiple(self, value: bool) -> None:
    for item in self.items:
      item.multiple = value
