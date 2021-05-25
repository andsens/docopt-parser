from ..identnode import IdentNode, ident
from .. import non_symbol_chars, char

class Command(IdentNode):
  illegal = non_symbol_chars

  def __init__(self, name):
    super().__init__(name)
    self.name = name

  def __repr__(self):
    return f'''<Command>: {self.name}'''

command = ident(Command.illegal, starts_with=char(illegal=Command.illegal | char('-'))).parsecmap(lambda n: Command(n))
