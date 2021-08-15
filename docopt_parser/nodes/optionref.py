from .identnode import IdentNode

class OptionRef(IdentNode):
  def __init__(self, option, ref, arg):
    super().__init__(option.ident)
    self.option = option
    self.ref = ref
    self.arg = arg

  def __repr__(self):
    return f'''<OptionRef>{self.repeatable_suffix}
  {self.indent(self.ref)}
  refarg: {self.arg}'''
