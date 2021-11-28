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

  def __iter__(self):
    yield 'type', 'optionref'
    yield 'repeatable', self.repeatable
    yield 'arg', self.arg
    yield 'ref', self.ref

  @property
  def multiple(self):
    return self.option.multiple

  @multiple.setter
  def multiple(self, value):
    self.option.multiple = value
