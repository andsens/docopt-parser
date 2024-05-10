import typing as T
import parsec as P
from docopt_parser import base
from docopt_parser.util import helpers, marks, parsers

class Argument(base.Leaf):
  @property
  def default(self) -> T.List[str] | None:
    if self._multiple:
      return []
    else:
      return None

  def __iter__(self):  # type: ignore
    yield from super().__iter__()
    yield 'default', self.default

wrapped_arg = (parsers.char('<') + base.ident(parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string).mark()

arg_letters = base.ident(illegal=parsers.non_symbol_chars).parsecmap(helpers.join_string).mark()

@P.generate('ARG')
def uppercase_arg() -> helpers.GeneratorParser[marks.MarkedTuple[str]]:
  name = yield P.lookahead(P.optional(arg_letters))
  if name is not None and name[1].isupper():
    return (yield arg_letters.desc('ARG'))
  else:
    yield P.fail_with('Not an argument')  # type: ignore
  return (((0, 0), '', (0, 0)))  # Will never return, this is just to make the typechecker happy

argument = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(lambda n: Argument(n))
