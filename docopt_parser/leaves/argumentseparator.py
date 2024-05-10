import typing as T
import parsec as P

from docopt_parser import base
from docopt_parser.util import parsers

class ArgumentSeparator(base.Leaf):
  @property
  def default(self) -> "T.Literal[0] | T.Literal[False]":
    if self._multiple:
      return 0
    else:
      return False

  def __iter__(self):  # type: ignore
    yield from super().__iter__()
    yield 'default', self.default

arg_separator = P.unit(parsers.string('--') << P.lookahead(parsers.non_symbol_chars)).mark() \
  .parsecmap(lambda n: ArgumentSeparator(n))
