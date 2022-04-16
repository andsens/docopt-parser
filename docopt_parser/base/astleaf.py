import typing as T
from abc import ABC, abstractmethod

IterVal = str | bool | T.Sequence["IterVal"] | T.Dict[str, "IterVal"] | None
DictGenerator = T.Generator[T.Tuple[str, IterVal], None, None]

class AstLeaf(ABC):
  repeatable: bool = False

  def indent(self, child: "AstLeaf" | T.Sequence["AstLeaf"], lvl: int = 1) -> str:
    if isinstance(child, AstLeaf):
      lines = repr(child).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)
    else:
      lines = '\n'.join(map(repr, child)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])

  @property
  def repeatable_suffix(self) -> str:
    return ' (repeatable)' if self.repeatable else ''

  @property
  def multiple_suffix(self) -> str:
    return '*' if getattr(self, 'multiple', False) else ''

  @abstractmethod
  def __iter__(self) -> DictGenerator:
    pass
