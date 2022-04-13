from typing import Iterator, Union

from docopt_parser import base, marked, parsers

illegal = parsers.non_symbol_chars

class Command(base.IdentNode):
  __name: marked.Marked
  multiple: bool = False
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple):
    super().__init__(name[1])
    self.__name = marked.Marked(name)
    self.mark = marked.Mark(self.__name.start, self.__name.end)

  @property
  def name(self):
    return self.__name.txt

  def __repr__(self) -> str:
    return f'''<Command{self.multiple_suffix}>{self.repeatable_suffix}: {self.name}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool]]]:
    yield 'name', self.name
    yield 'multiple', self.multiple

command = base.ident(illegal, starts_with=parsers.char(illegal=illegal | parsers.char('-'))).mark() \
  .parsecmap(lambda n: Command(n))
