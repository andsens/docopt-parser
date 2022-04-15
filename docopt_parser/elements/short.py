from parsec import optional, unit

from docopt_parser import base, elements, parsers, marked

illegal = parsers.non_symbol_chars | parsers.char(',=-')

# The reference implementation only allows inline specifying long options with arguments.
# Since supporting short options as well does not introduce any ambiguity I chose to implement it.
# TODO: Emit a warning when this additional feature is used
inline_short_option_spec = (
  unit(parsers.char('-') >> parsers.char(illegal=illegal)).mark()
  + optional((parsers.char('=') >> elements.argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
inline_shortlist_short_option_spec = (
  parsers.char(illegal=illegal).mark() + optional((parsers.char('=') >> elements.argument))
).desc('short option (-a)').parsecmap(lambda n: Short(*n))


class Short(base.IdentNode):
  __name: marked.Marked[str]
  arg: elements.Argument | None

  def __init__(self, name: marked.MarkedTuple[str], arg: elements.Argument | None):
    super().__init__(f'-{name[1]}')
    self.__name = marked.Marked(name)
    self.arg = arg

  @property
  def name(self):
    return self.__name.elm

  @property
  def mark(self) -> marked.Mark:
    return self.__name

  @property
  def expects_arg(self):
    return self.arg is not None

  def __repr__(self):
    return f'''-{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
