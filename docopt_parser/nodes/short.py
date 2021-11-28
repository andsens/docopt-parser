from .identnode import IdentNode
from . import non_symbol_chars, char, unit
from parsec import optional
from .argument import argument

illegal = non_symbol_chars | char(',=-')

# The reference implementation only allows inline specifying long options with arguments.
# Since supporting short options as well does not introduce any ambiguity I chose to implement it.
# TODO: Emit a warning when this additional feature is used
inline_short_option_spec = (
  unit(char('-') >> char(illegal=illegal)) + optional((char('=') >> argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
inline_shortlist_short_option_spec = (
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

  def __iter__(self):
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
