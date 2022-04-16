import parsec as P

from docopt_parser import base, leaves, marks, parsers, helpers

illegal = parsers.non_symbol_chars | parsers.char(',=-')

inline_short_option_spec = (
  P.unit(parsers.char('-') + parsers.char(illegal=illegal)).parsecmap(helpers.join_string).mark()
).desc('short option (-a)').parsecmap(lambda n: Short(n, None))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
# Prefix the parse result with a "-" in order to forward the proper identifier to Short()
inline_shortlist_short_option_spec = (
  parsers.char(illegal=illegal).parsecmap(lambda n: '-' + n).mark() + P.optional((parsers.char('=') >> leaves.argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))


class Short(base.IdentNode):
  arg: leaves.Argument | None
  ref: "leaves.DocumentedOption | None"

  def __init__(self, name: marks.MarkedTuple[str], arg: leaves.Argument | None):
    super().__init__(name)
    self.arg = arg
    self.ref = None

  @property
  def ident(self):
    if self.ref is not None:
      return self.ref.ident
    else:
      return self._ident

  @property
  def expects_arg(self):
    return self.arg is not None

  def __repr__(self):
    return f'''{self.ident}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self):
    yield from super().__iter__()
    yield 'arg', dict(self.arg) if self.arg else None
