from typing import Iterator
from .astleaf import AstLeaf
from ..marked import Mark, Marked, MarkedTuple
from . import lookahead, string, unit, non_symbol_chars

arg_separator = unit(string('--') << lookahead(non_symbol_chars)).mark().parsecmap(lambda n: ArgumentSeparator(n))

class ArgumentSeparator(AstLeaf):
  __name: Marked
  multiple: bool = False
  mark: Mark

  def __init__(self, name: MarkedTuple):
    super().__init__()
    self.__name = Marked(name)
    self.mark = Mark(self.__name.start, self.__name.end)

  def __repr__(self) -> str:
    return f'<ArgumentSeparator{self.multiple_suffix}>{self.repeatable_suffix}'

  def __iter__(self) -> Iterator[str]:
    yield '--'
