from typing import Iterator
from .astleaf import AstLeaf
from . import lookahead, string, unit, non_symbol_chars

arg_separator = unit(string('--') << lookahead(non_symbol_chars)).parsecmap(lambda n: ArgumentSeparator())

class ArgumentSeparator(AstLeaf):
  multiple: bool = False

  def __repr__(self) -> str:
    return f'<ArgumentSeparator{self.multiple_suffix}>{self.repeatable_suffix}'

  def __iter__(self) -> Iterator[str]:
    yield '--'
