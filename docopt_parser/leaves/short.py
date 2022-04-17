import typing as T
import parsec as P

from docopt_parser import base, leaves, marks, parsers, helpers

illegal = parsers.non_symbol_chars | parsers.char(',=-')

no_equals = (
  P.lookahead(parsers.char(illegal='='))
  ^ P.fail_with('Short option arguments must be separated with a space')  # type: ignore
).parsecmap(lambda _: '')  # type: ignore

usage_short_option = (
  (P.unit(parsers.char('-') + parsers.char(illegal=illegal)) + no_equals).parsecmap(helpers.join_string).mark()
).desc('short option (-a)').parsecmap(lambda n: Short(n, None))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
# Prefix the parse result with a "-" in order to forward the proper identifier to Short()
usage_shortlist_option = (
  (parsers.char(illegal=illegal) + no_equals).parsecmap(lambda n: '-' + n[0]).mark()
).desc('short option (-a)').parsecmap(lambda n: Short(n, None))


class Short(base.IdentNode):
  arg: "leaves.Argument | None"
  ref: "leaves.DocumentedOption | None"

  def __init__(self, name: marks.MarkedTuple[str], arg: "leaves.Argument | None"):
    super().__init__(name)
    self.arg = arg
    self.ref = None

  @property
  def multiple(self) -> bool:
    return self._multiple

  @multiple.setter
  def multiple(self, val: bool):
    self._multiple = val
    if self.ref:
      self.ref.multiple = val

  def __hash__(self) -> int:
    if self.ref is not None:
      return self.ref.__hash__()
    else:
      return super().__hash__()

  def __eq__(self, other: T.Any) -> bool:
    if self.ref is not None:
      return self.ref.__eq__(other)
    else:
      return super().__eq__(other)

  @property
  def expects_arg(self):
    return self.arg is not None

  def __repr__(self):
    arg_suffix = ' ' + self.arg.ident if self.arg is not None else ''
    return f'''{self.ident}{self.multiple_suffix}{arg_suffix}'''

  def __iter__(self):
    yield from super().__iter__()
    if self.arg:
      yield 'arg', self.arg.ident
    if self.ref:
      yield 'ref', self.ref.dict
