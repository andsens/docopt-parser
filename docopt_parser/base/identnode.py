import typing as T
from parsec import Parser, many, fail_with  # type: ignore

from docopt_parser import helpers, marks, parsers, base


def ident(illegal: "str | Parser[str | None] | None", starts_with: "Parser[str] | None" = None) -> "Parser[str]":
  if starts_with is None:
    starts_with = parsers.char(illegal=illegal)
  p = (
    starts_with
    + many(parsers.char(illegal=illegal))
  ).parsecmap(helpers.join_string)
  return p ^ fail_with('identifier')


class IdentNode(base.AstLeaf):
  _ident: str

  def __init__(self, ident: marks.MarkedTuple[str]):
    super().__init__((ident[0], ident[2]))
    self._ident = ident[1]

  @property
  def ident(self):
    return self._ident

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other: T.Any) -> bool:
    return isinstance(other, IdentNode) and self.ident == other.ident

  def __repr__(self):
    return super().__repr__() + f': {self.ident}'

  def __iter__(self):
    yield from super().__iter__()
    yield 'ident', self.ident
