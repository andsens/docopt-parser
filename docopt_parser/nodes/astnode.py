from typing import Callable, Iterable, TypeVar
from .astleaf import AstLeaf

T = TypeVar('T')
class AstNode(AstLeaf):
  items: Iterable[AstLeaf]

  def __init__(self, items: Iterable[AstLeaf]):
    self.items = items

  def reduce(self, function: Callable[[T], T], initializer: T) -> T:
    items = iter(self.items)
    if initializer is None:
      value = next(items)
    else:
      value = initializer
    for item in items:
      if isinstance(item, AstNode):
        value = function(value, item.reduce(function, value))
      else:
        value = function(value, item)
    return value
