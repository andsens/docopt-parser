from docopt_parser import base

class Sequence(base.AstNode):
  def __repr__(self) -> str:
    return f'''<Sequence>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'sequence'
    yield 'repeatable', self.repeatable
    yield 'items', [dict(item) for item in self.items]
