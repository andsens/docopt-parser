from ..astnode import AstNode
from .. import string

class OptionsShortcut(AstNode):
  def __repr__(self):
    return '<OptionsShortcut>'

  def new(args):
    return OptionsShortcut()

  shortcut = string('options').parsecmap(new)
