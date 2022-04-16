from docopt_parser import base


class Optional(base.AstNode):
  def __repr__(self):
    return f'''<Optional>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'optional'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]
