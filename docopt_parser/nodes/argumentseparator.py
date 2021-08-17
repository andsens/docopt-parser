from .astleaf import AstLeaf
from . import lookahead, string, unit, non_symbol_chars

arg_separator = unit(string('--') << lookahead(non_symbol_chars)).parsecmap(lambda n: ArgumentSeparator())

class ArgumentSeparator(AstLeaf):
  multiple = False

  def __repr__(self):
    return f'<ArgumentSeparator{self.multiple_suffix}>{self.repeatable_suffix}'
