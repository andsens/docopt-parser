from .identnode import IdentNode, ident
from . import non_symbol_chars, char, string, unit
from parsec import optional
from .argument import argument


illegal = non_symbol_chars | char(',=')

inline_long_option_spec = (
  unit(string('--') >> ident(illegal)) + optional(char('=') >> argument)
).desc('long option (--long)').parsecmap(lambda n: Long(*n))

class Long(IdentNode):

  def __init__(self, name, arg):
    super().__init__(f'--{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''--{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self):
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
