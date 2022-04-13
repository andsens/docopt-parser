from typing import Generator, Iterator, Union
from parsec import Parser, generate, many1, optional

from docopt_parser import base, helpers, parsers, marked

class Argument(base.IdentNode):
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
    return f'''<Argument{self.multiple_suffix}>: {self.name}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool]]]:
    yield 'name', self.name
    yield 'multiple', self.multiple


illegal = parsers.non_symbol_chars

wrapped_arg = (parsers.char('<') + base.ident(illegal | parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string)

@generate('ARG')
def uppercase_arg() -> Generator[Parser, Parser, str]:
  name_p = many1(parsers.char(illegal=illegal)).parsecmap(helpers.join_string).desc('ARG')
  name = yield parsers.lookahead(optional(name_p))
  if name is not None and name.isupper():
    name = yield name_p
  else:
    yield parsers.fail_with('Not an argument')
  return name

argument = (wrapped_arg ^ uppercase_arg).mark().desc('argument').parsecmap(lambda n: Argument(n))
