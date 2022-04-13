from typing import Iterator

from docopt_parser import base, parsers, marked

arg_separator = parsers.unit(parsers.string('--') << parsers.lookahead(parsers.non_symbol_chars)).mark() \
  .parsecmap(lambda n: ArgumentSeparator(n))

class ArgumentSeparator(base.AstLeaf):
  __name: marked.Marked
  multiple: bool = False
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple):
    super().__init__()
    self.__name = marked.Marked(name)
    self.mark = marked.Mark(self.__name.start, self.__name.end)

  def __repr__(self) -> str:
    return f'<ArgumentSeparator{self.multiple_suffix}>{self.repeatable_suffix}'

  def __iter__(self) -> Iterator[str]:
    yield '--'
