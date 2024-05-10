import typing as T
from docopt_parser import base
from docopt_parser.util import marks

class Group(base.Node):
  items: T.Sequence[base.Node]

  def __init__(self, items: marks.MarkedTuple[T.Sequence[base.Node]]):
    super().__init__((items[0], items[2]))
    self.items = list(items[1])

  _T = T.TypeVar('_T')

  def reduce(self, function: T.Callable[[_T, base.Node], _T], memo: _T) -> _T:
    for item in iter(self.items):
      memo = function(memo, item)
      if isinstance(item, Group):
        memo = item.reduce(function, memo)
    return function(memo, self)

  _U = T.TypeVar('_U', bound=base.Node)
  _V = T.TypeVar('_V', bound="base.Node | None")

  def replace(self, function: T.Callable[[_U], _V]):
    new_items: T.List[base.Node] = []
    for item in self.items:
      if isinstance(item, Group):
        item = item.replace(function)
      else:
        item = function(item)  # type: ignore
      if item is not None:
        new_items.append(item)
    self.items = new_items
    return function(self)  # type: ignore

  def walk(self, function: T.Callable[[_U], None]):
    for item in self.items:
      if isinstance(item, Group):
        item.walk(function)
      else:
        function(item)  # type: ignore
    function(self)  # type: ignore

  def __repr__(self):
    return f'''<{str(type(self).__name__).capitalize()}>
{self.indent(self.items)}'''


  def __iter__(self) -> base.DictGenerator:
    yield from super().__iter__()
    yield 'item', [item.dict for item in self.items]
