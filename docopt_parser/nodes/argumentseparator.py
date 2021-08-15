from .astnode import AstNode
from . import lookahead, string, unit, non_symbol_chars

arg_separator = unit(string('--') << lookahead(non_symbol_chars)).parsecmap(lambda n: ArgumentSeparator())

class ArgumentSeparator(AstNode):
  def __repr__(self):
    return f'<ArgumentSeparator>{self.repeatable_suffix}'
