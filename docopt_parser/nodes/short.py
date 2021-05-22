from .identnode import IdentNode
from . import non_symbol_chars, char, string, lookahead
from parsec import generate, optional
from .argument import Argument

class Short(IdentNode):

  illegal = non_symbol_chars | char(',=-')

  def __init__(self, name, arg):
    super().__init__(f'-{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''-{self.name}
  arg: {self.arg}'''

  @property
  def usage_parser(self):
    return self._usage_parser(expect_dash=True)

  @property
  def nodash_usage_parser(self):
    return self._usage_parser(expect_dash=False)

  def _usage_parser(self, expect_dash=True):
    @generate(f'-{self.name}')
    def p():
      if expect_dash:
        yield string('-' + self.name).desc(f'-{self.name}')
      else:
        yield string(self.name).desc(f'-{self.name}')
      if self.arg is not None:
        yield (optional(char(' =')) >> Argument.arg).desc(f'argument ({self.arg.name})')
      return self
    return p

  usage = (
    char('-') >> char(illegal=illegal) + optional((char(' =') >> Argument.arg))
  ).desc('short option (-a)').parsecmap(lambda n: Short(*n))

  # Usage parser without the leading "-" to allow parsing "-abc" style option specs
  nodash_usage = (
    char(illegal=illegal) + optional((char(' =') >> Argument.arg))
  ).desc('short option (-a)').parsecmap(lambda n: Short(*n))

  @generate('short option (-s)')
  def options():
    argument = (char(' =') >> Argument.arg).desc('argument')
    yield string('-')
    name = yield char(illegal=Short.illegal)
    if (yield optional(lookahead(char('=')))) is not None:
      # Definitely an argument, make sure we fail with "argument expected"
      arg = yield argument
    else:
      arg = yield optional(argument)
    return Short(name, arg)
