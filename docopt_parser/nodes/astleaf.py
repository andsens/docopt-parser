from typing_extensions import Self

class AstLeaf(object):
  repeatable: bool = False

  def indent(self, child: Self, lvl: int = 1) -> str:
    if isinstance(child, list):
      lines = '\n'.join(map(repr, child)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
    else:
      lines = repr(child).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)

  @property
  def repeatable_suffix(self) -> str:
    return ' (repeatable)' if self.repeatable else ''

  @property
  def multiple_suffix(self) -> str:
    return '*' if hasattr(self, 'multiple') and self.multiple else ''
