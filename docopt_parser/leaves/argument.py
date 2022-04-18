import parsec as P

from docopt_parser import base, helpers, marks, parsers

class Argument(base.Leaf):
  def __init__(self, name: marks.MarkedTuple[str]):
    super().__init__(name)

illegal = parsers.non_symbol_chars

wrapped_arg = (parsers.char('<') + base.ident(parsers.char('>')) + parsers.char('>')) \
  .desc('<arg>').parsecmap(helpers.join_string).mark().desc('argument').parsecmap(lambda n: Argument(n))

@P.generate('ARG')
def uppercase_arg() -> helpers.GeneratorParser[Argument]:
  name_p = P.many1(parsers.char(illegal=illegal)).parsecmap(helpers.join_string).desc('ARG')
  name = yield P.lookahead(P.optional(name_p))
  if name is not None and name.isupper():
    return (yield name_p.mark().desc('argument').parsecmap(lambda n: Argument(n)))
  else:
    yield P.fail_with('Not an argument')  # type: ignore
  return Argument(((0, 0), '', (0, 0)))  # Will never return, this is just to make the typechecker happy

argument = (wrapped_arg ^ uppercase_arg)
