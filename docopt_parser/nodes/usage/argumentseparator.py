from ..astnode import AstNode
from .. import lookahead, string, char, nl, eof

class ArgumentSeparator(AstNode):
  def __repr__(self):
    return '<ArgumentSeparator>'

  def new(args):
    return ArgumentSeparator()

  separator = (lookahead(string('--') << char('| \n)()[]') | nl | eof()) >> string('--')).parsecmap(new)
