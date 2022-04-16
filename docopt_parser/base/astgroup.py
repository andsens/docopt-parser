import typing as T

from docopt_parser import base, marks

class AstGroup(base.AstNode):
  items: T.Sequence[base.AstNode]

  def __init__(self, items: marks.MarkedTuple[T.Sequence[base.AstNode]]):
    super().__init__((items[0], items[2]))
    self.items = list(items[1])

  _T = T.TypeVar('_T')

  def reduce(self, function: T.Callable[[_T, "base.AstNode"], _T], memo: _T) -> _T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, AstGroup):
        memo = item.reduce(function, memo)
    return memo

  def walk(self, function: T.Callable[["base.AstNode"], None]) -> None:
    for item in iter(self.items):
      if isinstance(item, AstGroup):
        item.walk(function)
      function(item)

  def __repr__(self):
    return f'''<{str(type(self).__name__).capitalize()}>{self.repeatable_suffix}
{self.indent(self.items)}'''


  def __iter__(self) -> base.DictGenerator:
    yield from super().__iter__()
    yield 'items', [dict(item) for item in self.items]
