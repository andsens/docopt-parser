from typing import Union
from parsec import Parser, many

from docopt_parser import helpers, parsers, base


def ident(illegal: Union[str, Parser, None], starts_with: Union[Parser, None] = None) -> Parser:
  if starts_with is None:
    starts_with = parsers.char(illegal=illegal)
  return (
    starts_with
    + many(parsers.char(illegal=illegal))
  ).parsecmap(helpers.flatten).parsecmap(helpers.join_string) ^ parsers.fail_with('identifier')


class IdentNode(base.AstLeaf):
  ident: str

  def __init__(self, ident: str):
    self.ident = ident

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other) -> bool:
    return isinstance(other, IdentNode) and self.ident == other.ident
