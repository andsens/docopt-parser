import typing as T
import parsec as P

from docopt_parser import base, helpers, parsers, marked

class Argument(base.IdentNode):
  __name: marked.Marked[str]
  multiple: bool = False

  def __init__(self, name: marked.MarkedTuple[str]):
    super().__init__(name[1])
    self.__name = marked.Marked(name)

  @property
  def name(self):
    return self.__name.elm

  @property
  def mark(self) -> marked.Mark:
    return self.__name

  def __repr__(self):
    return f'''<Argument{self.multiple_suffix}>: {self.name}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'name', self.name
    yield 'multiple', self.multiple


illegal = parsers.non_symbol_chars

wrapped_arg = (parsers.char('<') + base.ident(illegal | parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string)

@P.generate('ARG')
def uppercase_arg() -> helpers.GeneratorParser[str]:
  name_p = P.many1(parsers.char(illegal=illegal)).parsecmap(helpers.join_string).desc('ARG')
  name: str | None = yield P.lookahead(P.optional(name_p))
  if name is not None and name.isupper():
    return (yield name_p)
  else:
    yield P.fail_with('Not an argument')  # type: ignore
  return T.cast(str, name)

argument = (wrapped_arg ^ uppercase_arg).mark().desc('argument').parsecmap(lambda n: Argument(n))
