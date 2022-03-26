from typing import Union
from .astleaf import AstLeaf
from . import char, flatten, join_string, fail_with
from parsec import Parser, many


def ident(illegal: Union[str, Parser, None], starts_with: Union[Parser, None] = None) -> Parser:
  if starts_with is None:
    starts_with = char(illegal=illegal)
  return (
    starts_with
    + many(char(illegal=illegal))
  ).parsecmap(flatten).parsecmap(join_string) ^ fail_with('identifier')


class IdentNode(AstLeaf):
  ident: str

  def __init__(self, ident: str):
    self.ident = ident

  def __hash__(self) -> int:
    return hash(self.ident)

  def __eq__(self, other) -> bool:
    return isinstance(other, IdentNode) and self.ident == other.ident
