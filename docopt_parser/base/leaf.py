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

  # Intentionally not specifying a getter, it's an internal variable
  def set_multiple(self, val: bool):
    self._multiple = val

  @property
  def _multiple_suffix(self) -> str:
    # Remove multiple and use a setter instead
    return '*' if self._multiple else ''

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other: T.Any) -> bool:
    return isinstance(other, Leaf) and self.ident == other.ident

  def __repr__(self):
    return f'{str(type(self).__name__)}{self._multiple_suffix}: {self.ident}'

  def __iter__(self):  # type: ignore
    yield from super().__iter__()
    yield 'ident', self.ident

  _T = T.TypeVar('_T')

  def reduce(self, function: "T.Callable[[_T, base.Node], _T]", memo: _T) -> _T:
    return function(memo, self)

  _U = T.TypeVar('_U', bound="base.Node")
  _V = T.TypeVar('_V', bound="base.Node | None")

  def replace(self, function: T.Callable[[_U], _V]):
    return function(self)  # type: ignore

  def walk(self, function: T.Callable[[_U], None]):
    function(self)  # type: ignore
