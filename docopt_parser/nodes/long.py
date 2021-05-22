from .identnode import IdentNode, ident
from . import non_symbol_chars, char, string, lookahead
from parsec import generate, optional
from .argument import Argument

class Long(IdentNode):

  illegal = non_symbol_chars | char(',=')

  def __init__(self, name, arg):
    super().__init__(f'--{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''--{self.name}
  arg: {self.arg}'''

  @property
  def usage_parser(self):
    @generate(f'--{self.name}')
    def p():
      yield string('--' + self.name)
      if self.arg is not None:
        yield (char(' =') >> Argument.arg).desc(f'argument ({self.arg.name})')
      return self
    return p

  usage = (
    char('--') >> ident(illegal) + optional(char('=') >> Argument.arg)
  ).desc('long option (--long)').parsecmap(lambda n: Long(*n))

  @generate('long option (--long)')
  def options():
    argument = (char(' =') >> Argument.arg).desc('argument')
    yield string('--')
    name = yield ident(Long.illegal)
    if (yield optional(lookahead(char('=')))) is not None:
      # Definitely an argument, make sure we fail with "argument expected"
      arg = yield argument
    else:
      arg = yield optional(argument)
    return Long(name, arg)
