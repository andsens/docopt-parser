from .astnode import AstNode

class OptionRef(AstNode):
  def __init__(self, option, ref, arg):
    self.option = option
    self.ref = ref
    self.arg = arg

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.ref)}
  refarg: {self.arg}'''
