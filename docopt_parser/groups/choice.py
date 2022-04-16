from docopt_parser import base


class Choice(base.AstNode):
  def __repr__(self):
    return f'''<Choice>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'repeatable', self.repeatable
    yield 'type', 'choice'
    yield 'items', [dict(item) for item in self.items]
