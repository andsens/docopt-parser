from .identnode import IdentNode
from . import non_symbol_chars, char, string, lookahead, unit
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

  def _usage_ref(self, shorts_list):
    @generate(f'-{self.name}')
    def p():
      if shorts_list:
        yield string(self.name).desc(f'-{self.name}')
      else:
        yield string('-' + self.name).desc(f'-{self.name}')
      if self.arg is not None:
        return self, (yield (optional(char(' =')) >> Argument.arg).desc(f'argument ({self.arg.name})'))
      return self, None
    return p

  # The reference implementation only allows inline specifying long options with arguments.
  # Since supporting short options as well does not introduce any ambiguity I chose to implement it.
  # TODO: Emit a warning that when this additional feature is used
  inline_spec_usage = (
    unit(char('-') >> char(illegal=illegal)) + optional((char('=') >> Argument.arg))
  ).desc('short option (-a)').parsecmap(lambda n: Short(*n))

  # Usage parser without the leading "-" to allow parsing "-abc" style option specs
  shorts_list_inline_spec_usage = (
    char(illegal=illegal) + optional((char('=') >> Argument.arg))
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
