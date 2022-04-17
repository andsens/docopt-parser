from docopt_parser.base.astelement import AstElement


class AstNode(AstElement):
  repeatable: bool = False

  @property
  def repeatable_suffix(self) -> str:
    return ' (repeatable)' if self.repeatable else ''

  def __iter__(self):
    yield from super().__iter__()
    if self.repeatable:
      yield 'repeatable', self.repeatable
