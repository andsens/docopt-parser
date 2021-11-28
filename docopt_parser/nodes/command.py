from .identnode import IdentNode, ident
from . import non_symbol_chars, char

illegal = non_symbol_chars

class Command(IdentNode):
  multiple = False

  def __init__(self, name):
    super().__init__(name)
    self.name = name

  def __repr__(self):
    return f'''<Command{self.multiple_suffix}>{self.repeatable_suffix}: {self.name}'''

  def __iter__(self):
    yield 'name', self.name
    yield 'multiple', self.multiple

command = ident(illegal, starts_with=char(illegal=illegal | char('-'))).parsecmap(lambda n: Command(n))
