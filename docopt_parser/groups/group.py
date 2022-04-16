from docopt_parser import base


class Group(base.AstNode):
  def __repr__(self):
    return f'''<Group>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'repeatable', self.repeatable
    yield 'type', 'group'
    yield 'items', [dict(item) for item in self.items]
