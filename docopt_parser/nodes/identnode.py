from .astnode import AstNode
from . import char, flatten, join_string, fail_with
from parsec import many


def ident(illegal, starts_with=None):
  if starts_with is None:
    starts_with = char(illegal=illegal)
  return (
    starts_with
    + many(char(illegal=illegal))
  ).parsecmap(flatten).parsecmap(join_string) ^ fail_with('identifier')


class IdentNode(AstNode):
  def __init__(self, ident):
    super().__init__()
    self.ident = ident

  def __hash__(self):
    return hash(self.ident)
