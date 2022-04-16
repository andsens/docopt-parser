from docopt_parser.base.astnode import AstNode

class AstLeaf(AstNode):
  multiple: bool = False

  @property
  def multiple_suffix(self) -> str:
    return '*' if self.multiple else ''

  def __iter__(self):
    yield from super().__iter__()
    yield 'multiple', self.multiple

  def __repr__(self):
    return f'<{str(type(self).__name__)}{self.multiple_suffix}>{self.repeatable_suffix}'
