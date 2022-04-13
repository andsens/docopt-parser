from typing import Callable, Iterable, TypeVar
from .astleaf import AstLeaf

T = TypeVar('T')
class AstNode(AstLeaf):
  items: Iterable[AstLeaf]

  def __init__(self, items: Iterable[AstLeaf]):
    self.items = items

  def reduce(self, function: Callable[[T], T], memo: T = None) -> T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, AstNode):
        memo = item.reduce(function, memo)
    return memo
