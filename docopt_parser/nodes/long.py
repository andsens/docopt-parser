from .identnode import IdentNode, ident
from . import non_symbol_chars, char, string, lookahead, unit
from parsec import generate, optional
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
    return f'''--{self.name}
  arg: {self.arg}'''

  @property
  def usage_ref(self):
    @generate(f'--{self.name}')
    def p():
      # The lookahead is to ensure that we don't consume a prefix of another option
      # e.g. --ab matching --abc
      yield unit(string('--' + self.name) << lookahead(illegal))
      if self.arg is not None:
        return self, (yield (char(' =') >> argument).desc(f'argument ({self.arg.name})'))
      return self, None
    return p
