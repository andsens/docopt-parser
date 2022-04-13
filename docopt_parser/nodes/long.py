from typing import Iterator, Union
from ..marked import Mark, Marked, MarkedTuple
from .identnode import IdentNode, ident
from . import non_symbol_chars, char, string, unit
from parsec import optional
from .argument import Argument, argument


illegal = non_symbol_chars | char(',=')

inline_long_option_spec = (
  unit(string('--') >> ident(illegal)).mark() + optional(char('=') >> argument)
).desc('long option (--long)').parsecmap(lambda n: Long(*n))

class Long(IdentNode):
  __name: Marked
  arg: Union[Argument, None]
  mark: Mark

  def __init__(self, name: MarkedTuple, arg: Union[Argument, None]):
    super().__init__(f'--{name[1]}')
    self.__name = Marked(name)
    self.arg = arg
    self.mark = Mark(self.__name.start, self.arg.mark.end if self.arg else self.__name.end)

  @property
  def name(self):
    return self.__name.txt

  def __repr__(self) -> str:
    return f'''--{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, dict]]]:
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
