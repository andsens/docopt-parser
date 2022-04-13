from typing import Callable, Iterable, TypeVar

from docopt_parser import base

T = TypeVar('T')
class AstNode(base.AstLeaf):
  items: Iterable[base.AstLeaf]

  def __init__(self, items: Iterable[base.AstLeaf]):
    self.items = items

  def reduce(self, function: Callable[[T], T], memo: T = None) -> T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, AstNode):
        memo = item.reduce(function, memo)
    return memo
