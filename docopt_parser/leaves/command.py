import typing as T

from docopt_parser import base
from docopt_parser.util import parsers

class Command(base.Leaf):
  @property
  def default(self) -> "T.Literal[0] | T.Literal[False]":
    if self._multiple:
      return 0
    else:
      return False

  def __iter__(self):  # type: ignore
    yield from super().__iter__()
    yield 'default', self.default

command = base.ident(
  parsers.non_symbol_chars, starts_with=parsers.char(illegal=parsers.non_symbol_chars)
).mark().parsecmap(lambda n: Command(n))
