from typing import cast
from parsec import generate, many1, optional, lookahead, fail_with  # type: ignore

from docopt_parser import base, helpers, parsers, marked

class Argument(base.IdentNode):
  __name: marked.Marked[str]
  multiple: bool = False
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple[str]):
    super().__init__(name[1])
    self.__name = marked.Marked(name)
    self.mark = marked.Mark(self.__name.start, self.__name.end)

  @property
  def name(self):
    return self.__name.elm

  def __repr__(self):
    return f'''<Argument{self.multiple_suffix}>: {self.name}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'name', self.name
    yield 'multiple', self.multiple


illegal = parsers.non_symbol_chars

wrapped_arg = (parsers.char('<') + base.ident(illegal | parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string)

@generate('ARG')
def uppercase_arg() -> helpers.GeneratorParser[str]:
  name_p = many1(parsers.char(illegal=illegal)).parsecmap(helpers.join_string).desc('ARG')
  name: str | None = yield lookahead(optional(name_p))
  if name is not None and name.isupper():
    return (yield name_p)
  else:
    yield fail_with('Not an argument')
  return cast(str, name)

argument = (wrapped_arg ^ uppercase_arg).mark().desc('argument').parsecmap(lambda n: Argument(n))
