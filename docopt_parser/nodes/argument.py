from typing import Generator, Iterator, Union
from .identnode import IdentNode, ident
from parsec import Parser, generate, many1, optional
from . import non_symbol_chars, char, join_string, lookahead, fail_with

class Argument(IdentNode):
  multiple: bool = False

  def __init__(self, name: str):
    super().__init__(name)
    self.name = name

  def __repr__(self) -> str:
    return f'''<Argument{self.multiple_suffix}>: {self.name}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool]]]:
    yield 'name', self.name
    yield 'multiple', self.multiple


illegal = non_symbol_chars

wrapped_arg = (char('<') + ident(illegal | char('>')) + char('>')).desc('<arg>').parsecmap(join_string)

@generate('ARG')
def uppercase_arg() -> Generator[Parser, Parser, str]:
  name_p = many1(char(illegal=illegal)).parsecmap(join_string).desc('ARG')
  name = yield lookahead(optional(name_p))
  if name is not None and name.isupper():
    name = yield name_p
  else:
    yield fail_with('Not an argument')
  return name

argument = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(lambda n: Argument(n))
