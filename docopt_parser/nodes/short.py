from .identnode import IdentNode
from . import non_symbol_chars, char, string, unit
from parsec import generate, optional
from .argument import argument

illegal = non_symbol_chars | char(',=-')

# The reference implementation only allows inline specifying long options with arguments.
# Since supporting short options as well does not introduce any ambiguity I chose to implement it.
# TODO: Emit a warning when this additional feature is used
inline_short_option_spec = (
  unit(char('-') >> char(illegal=illegal)) + optional((char('=') >> argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
shorts_list_inline_short_option_spec = (
  char(illegal=illegal) + optional((char('=') >> argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))


class Short(IdentNode):

  def __init__(self, name, arg):
    super().__init__(f'-{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''-{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def _usage_ref(self, shorts_list):
    @generate(f'-{self.name}')
    def p():
      if shorts_list:
        yield string(self.name).desc(f'-{self.name}')
      else:
        yield string('-' + self.name).desc(f'-{self.name}')
      if self.arg is not None:
        return self, (yield (optional(char(' =')) >> argument).desc(f'argument ({self.arg.name})'))
      return self, None
    return p
