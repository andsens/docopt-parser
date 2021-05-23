from ..astnode import AstNode
from .. import lookahead, string, unit, non_symbol_chars

class ArgumentSeparator(AstNode):
  def __repr__(self):
    return '<ArgumentSeparator>'

  separator = unit(string('--') << lookahead(non_symbol_chars)).parsecmap(lambda n: ArgumentSeparator())
