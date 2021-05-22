from ..astnode import AstNode

class OptionRef(AstNode):
  def __init__(self, option, arg):
    self.option = option
    self.arg = arg

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.option.short or self.option.long)}'''
