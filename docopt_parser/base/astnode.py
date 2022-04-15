from typing import Callable, List, TypeVar

from docopt_parser import base

class AstNode(base.AstLeaf):
  items: List[base.AstLeaf]

  def __init__(self, items: List[base.AstLeaf]):
    super().__init__()
    self.items = items

  T = TypeVar('T')

  def reduce(self, function: Callable[[T, "base.AstLeaf"], T], memo: T) -> T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, AstNode):
        memo = item.reduce(function, memo)
    return memo

  def walk(self, function: Callable[["base.AstLeaf"], None]) -> None:
    for item in iter(self.items):
      if isinstance(item, AstNode):
        item.walk(function)
      function(item)
