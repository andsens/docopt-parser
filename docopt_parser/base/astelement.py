import typing as T
from abc import ABC

from docopt_parser import marks

IterVal = str | bool | T.List["IterVal"] | T.Dict[str, "IterVal"] | None
DictGenerator = T.Generator[T.Tuple[str, IterVal], None, None]

class AstElement(ABC):
  mark: marks.Range

  def __init__(self, range: marks.RangeTuple):
    super().__init__()
    self.mark = marks.Range(range)

  def __iter__(self) -> DictGenerator:
    yield 'type', str(type(self).__name__).lower()

  def indent(self, child: "AstElement" | T.Sequence["AstElement"], lvl: int = 1) -> str:
    if isinstance(child, AstElement):
      lines = repr(child).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)
    else:
      lines = '\n'.join(map(repr, child)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
