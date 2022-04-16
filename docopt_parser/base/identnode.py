import typing as T
from parsec import Parser, many, fail_with  # type: ignore

from docopt_parser import helpers, parsers, base


def ident(illegal: "str | Parser[str | None] | None", starts_with: "Parser[str] | None" = None) -> "Parser[str]":
  if starts_with is None:
    starts_with = parsers.char(illegal=illegal)
  p = (
    starts_with
    + many(parsers.char(illegal=illegal))
  ).parsecmap(helpers.join_string)
  return p ^ fail_with('identifier')


class IdentNode(base.AstLeaf):
  ident: str

  def __init__(self, ident: str):
    super().__init__()
    self.ident = ident

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other: T.Any) -> bool:
    return isinstance(other, IdentNode) and self.ident == other.ident
