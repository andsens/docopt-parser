import typing as T

from docopt_parser import base

class AstNode(base.AstLeaf):
  items: T.List[base.AstLeaf]

  def __init__(self, items: T.Sequence[base.AstLeaf]):
    super().__init__()
    self.items = list(items)

  _T = T.TypeVar('_T')

  def reduce(self, function: T.Callable[[_T, "base.AstLeaf"], _T], memo: _T) -> _T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, AstNode):
        memo = item.reduce(function, memo)
    return memo

  def walk(self, function: T.Callable[["base.AstLeaf"], None]) -> None:
    for item in iter(self.items):
      if isinstance(item, AstNode):
        item.walk(function)
      function(item)
