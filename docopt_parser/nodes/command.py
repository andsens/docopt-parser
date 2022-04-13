from typing import Iterator, Union
from .identnode import IdentNode, ident
from ..marked import Mark, Marked, MarkedTuple
from . import non_symbol_chars, char

illegal = non_symbol_chars

class Command(IdentNode):
  __name: Marked
  multiple: bool = False
  mark: Mark

  def __init__(self, name: MarkedTuple):
    super().__init__(name[1])
    self.__name = Marked(name)
    self.mark = Mark(self.__name.start, self.__name.end)

  @property
  def name(self):
    return self.__name.txt

  def __repr__(self) -> str:
    return f'''<Command{self.multiple_suffix}>{self.repeatable_suffix}: {self.name}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool]]]:
    yield 'name', self.name
    yield 'multiple', self.multiple

command = ident(illegal, starts_with=char(illegal=illegal | char('-'))).mark().parsecmap(lambda n: Command(n))
