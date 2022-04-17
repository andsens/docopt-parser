import typing as T
import parsec as P

from docopt_parser import base, helpers, marks, parsers

class Argument(base.Leaf):
  def __init__(self, name: marks.MarkedTuple[str]):
    super().__init__(name)

illegal = parsers.non_symbol_chars

wrapped_arg = (parsers.char('<') + base.ident(illegal | parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string)

@P.generate('ARG')
def uppercase_arg() -> helpers.GeneratorParser[str]:
  name_p = P.many1(parsers.char(illegal=illegal)).parsecmap(helpers.join_string).desc('ARG')
  name = yield P.lookahead(P.optional(name_p))
  if name is not None and name.isupper():
    return (yield name_p)
  else:
    yield P.fail_with('Not an argument')  # type: ignore
  return T.cast(str, name)

argument = (wrapped_arg ^ uppercase_arg).mark().desc('argument').parsecmap(lambda n: Argument(n))
