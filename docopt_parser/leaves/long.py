import parsec as P

from docopt_parser import base, leaves, marks, parsers, helpers


illegal = parsers.non_symbol_chars | parsers.char(',=')

usage_long_option = (
  P.unit(
    parsers.string('--') + base.ident(illegal)
  ).parsecmap(helpers.join_string).mark() + P.optional(parsers.char('=') >> leaves.argument)
).desc('long option (--long)').parsecmap(lambda n: Long(*n))

class Long(base.Option):
  arg: "leaves.Argument | None"
  ref: "leaves.DocumentedOption | None"

  def __init__(self, name: marks.MarkedTuple[str], arg: "leaves.Argument | None"):
    super().__init__(name)
    self.arg = arg
    self.ref = None

  @property
  def expects_arg(self):
    return self.arg is not None

  @property
  def default(self) -> "str | None":
    if self.ref is not None:
      return self.ref.default

  def __repr__(self):
    arg_suffix = ' ' + self.arg.ident if self.arg is not None else ''
    return f'''{self.ident}{self.multiple_suffix}{arg_suffix}'''

  def __iter__(self):
    yield from super().__iter__()
    if self.arg:
      yield 'arg', self.arg.ident
    if self.ref:
      yield 'ref', self.ref.dict
