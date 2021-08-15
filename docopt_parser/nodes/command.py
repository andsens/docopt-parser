from .identnode import IdentNode, ident
from . import non_symbol_chars, char

illegal = non_symbol_chars

class Command(IdentNode):
  def __init__(self, name):
    super().__init__(name)
    self.name = name

  def __repr__(self):
    return f'''<Command>{self.repeatable_suffix}: {self.name}'''

command = ident(illegal, starts_with=char(illegal=illegal | char('-'))).parsecmap(lambda n: Command(n))
