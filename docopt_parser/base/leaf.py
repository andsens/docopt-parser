import typing as T
import parsec as P

from docopt_parser import base
from docopt_parser.util import helpers, marks, parsers


def ident(
  illegal: "str | P.Parser[T.Any] | None",
  starts_with: "P.Parser[str] | P.Parser[str | None] | None" = None
) -> "P.Parser[str]":
  if starts_with is None:
    starts_with = parsers.char(illegal=illegal)
  p = (
    starts_with
    + P.many(parsers.char(illegal=illegal))
  ).parsecmap(helpers.join_string)
  return p ^ P.fail_with('identifier')  # type: ignore

class Leaf(base.Node):
  ident: str
  _multiple: bool = False

  def __init__(self, ident: marks.MarkedTuple[str]):
    super().__init__((ident[0], ident[2]))
    self.ident = ident[1]

  @property
  def multiple(self) -> bool:
    return self._multiple

  @multiple.setter
  def multiple(self, val: bool):
    self._multiple = val

  @property
  def multiple_suffix(self) -> str:
    return '*' if self.multiple else ''

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other: T.Any) -> bool:
    return isinstance(other, Leaf) and self.ident == other.ident

  def __repr__(self):
    return f'{str(type(self).__name__)}{self.multiple_suffix}: {self.ident}'

  def __iter__(self):
    yield from super().__iter__()
    yield 'ident', self.ident
    if self.multiple:
      yield 'multiple', self.multiple
