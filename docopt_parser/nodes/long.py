from .identnode import IdentNode, ident
from . import non_symbol_chars, char, string, lookahead, unit
from parsec import generate, optional
from .argument import argument

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
  def usage_ref(self):
    @generate(f'--{self.name}')
    def p():
      # The lookahead is to ensure that we don't consume a prefix of another option
      # e.g. --ab matching --abc
      yield unit(string('--' + self.name) << lookahead(Long.illegal))
      if self.arg is not None:
        return self, (yield (char(' =') >> argument).desc(f'argument ({self.arg.name})'))
      return self, None
    return p

  inline_spec_usage = (
    unit(string('--') >> ident(illegal)) + optional(char('=') >> argument)
  ).desc('long option (--long)').parsecmap(lambda n: Long(*n))

  @generate('long option (--long)')
  def options():
    argspec = (char(' =') >> argument).desc('argument')
    yield string('--')
    name = yield ident(Long.illegal)
    if (yield optional(lookahead(char('=')))) is not None:
      # Definitely an argument, make sure we fail with "argument expected"
      arg = yield argspec
    else:
      arg = yield optional(argspec)
    return Long(name, arg)
