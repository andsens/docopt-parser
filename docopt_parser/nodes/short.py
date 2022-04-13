from typing import Iterator, Union
from .identnode import IdentNode
from . import non_symbol_chars, char, unit
from parsec import optional
from .argument import Argument, argument
from ..marked import Mark, Marked, MarkedTuple

illegal = non_symbol_chars | char(',=-')

# The reference implementation only allows inline specifying long options with arguments.
# Since supporting short options as well does not introduce any ambiguity I chose to implement it.
# TODO: Emit a warning when this additional feature is used
inline_short_option_spec = (
  unit(char('-') >> char(illegal=illegal)).mark() + optional((char('=') >> argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
inline_shortlist_short_option_spec = (
  char(illegal=illegal).mark() + optional((char('=') >> argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))


class Short(IdentNode):
  __name: Marked
  arg: Union[Argument, None]
  mark: Mark

  def __init__(self, name: MarkedTuple, arg: Union[Argument, None]):
    super().__init__(f'-{name[1]}')
    self.__name = Marked(name)
    self.arg = arg
    self.mark = Mark(self.__name.start, self.arg.mark.end if self.arg else self.__name.end)

  @property
  def name(self):
    return self.__name.txt

  def __repr__(self) -> str:
    return f'''-{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool]]]:
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
