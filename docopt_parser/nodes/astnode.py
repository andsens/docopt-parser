from .astleaf import AstLeaf

class AstNode(AstLeaf):
  def __init__(self, items):
    self.items = items

  def reduce(self, function, initializer):
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
