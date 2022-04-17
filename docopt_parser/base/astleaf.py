from docopt_parser.base.astnode import AstNode

class AstLeaf(AstNode):
  _multiple: bool = False

  @property
  def multiple(self) -> bool:
    return self._multiple

  @multiple.setter
  def multiple(self, val: bool):
    self._multiple = val

  @property
  def multiple_suffix(self) -> str:
    return '*' if self.multiple else ''

  def __iter__(self):
    yield from super().__iter__()
    if self.multiple:
      yield 'multiple', self.multiple

  def __repr__(self):
    return f'<{str(type(self).__name__)}{self.multiple_suffix}>{self.repeatable_suffix}'
