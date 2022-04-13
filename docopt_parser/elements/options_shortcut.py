from typing import Iterator, Union

from docopt_parser import elements, groups, parsers, marked

options_shortcut = parsers.string('options').mark().desc('options shortcut').parsecmap(lambda n: OptionsShortcut(n))

class OptionsShortcut(groups.Optional):
  __name: marked.Marked
  options: list[elements.DocumentedOption]
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple):
    self.options = []
    self.__name = marked.Marked(name)
    self.mark = marked.Mark(self.__name.start, self.__name.end)

  @property
  def items(self) -> list[elements.DocumentedOption]:
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
