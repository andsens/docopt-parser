from .astleaf import AstLeaf
from . import char, flatten, join_string, fail_with
from parsec import many


def ident(illegal, starts_with=None):
  if starts_with is None:
    starts_with = char(illegal=illegal)
  return (
    starts_with
    + many(char(illegal=illegal))
  ).parsecmap(flatten).parsecmap(join_string) ^ fail_with('identifier')


class IdentNode(AstLeaf):
  def __init__(self, ident):
    self.ident = ident

  def __hash__(self):
    return hash(self.ident)

  def __eq__(self, other):
    return isinstance(other, IdentNode) and self.ident == other.ident
