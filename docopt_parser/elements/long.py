from typing import Iterator, Union
from parsec import optional, unit

from docopt_parser import base, elements, parsers, marked


illegal = parsers.non_symbol_chars | parsers.char(',=')

inline_long_option_spec = (
  unit(parsers.string('--') >> base.ident(illegal)).mark() + optional(parsers.char('=') >> elements.argument)
).desc('long option (--long)').parsecmap(lambda n: Long(*n))

class Long(base.IdentNode):
  __name: marked.Marked
  arg: Union[elements.Argument, None]
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple, arg: Union[elements.Argument, None]):
    super().__init__(f'--{name[1]}')
    self.__name = marked.Marked(name)
    self.arg = arg
    self.mark = marked.Mark(self.__name.start, self.arg.mark.end if self.arg else self.__name.end)

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
