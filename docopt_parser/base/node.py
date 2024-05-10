import typing as T
import abc

from docopt_parser.util import marks

IterVal = T.Union[
  str, bool, T.Literal[0], T.Literal[False], T.List[str], None,
  T.List["IterVal"], T.Dict[str, "IterVal"]
]
DictGenerator = T.Generator[T.Tuple[str, IterVal], None, None]

class Node(abc.ABC):
  mark: marks.Range
  _previous_dict: "T.Dict[str, IterVal] | None" = None

  def __init__(self, range: marks.RangeTuple):
    super().__init__()
    self.mark = marks.Range(range)

  def __iter__(self) -> DictGenerator:
    yield 'type', str(type(self).__name__).lower()

  def indent(self, child: "Node | T.Sequence[Node]", lvl: int = 1) -> str:
    if isinstance(child, Node):
      lines = repr(child).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)
    else:
      lines = '\n'.join(map(repr, child)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])

  @property
  def dict(self) -> "T.Dict[str, IterVal]":
    new_dict = dict(self)
    if self._previous_dict is None or new_dict != self._previous_dict:
      self._previous_dict = new_dict
    return self._previous_dict

  _T = T.TypeVar('_T')

  @abc.abstractmethod
  def reduce(self, function: "T.Callable[[_T, Node], _T]", memo: _T) -> _T:
    pass

  _U = T.TypeVar('_U', bound="Node")
  _V = T.TypeVar('_V', bound="Node | None")

  def replace(self, function: T.Callable[[_U], _V]) -> _V:
    return function(self)  # type: ignore

  def walk(self, function: T.Callable[[_U], None]):
    pass
