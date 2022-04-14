from parsec import optional, unit

from docopt_parser import base, elements, parsers, marked


illegal = parsers.non_symbol_chars | parsers.char(',=')

inline_long_option_spec = (
  unit(parsers.string('--') >> base.ident(illegal)).mark() + optional(parsers.char('=') >> elements.argument)
).desc('long option (--long)').parsecmap(lambda n: Long(*n))

class Long(base.IdentNode):
  __name: marked.Marked[str]
  arg: elements.Argument | None
  mark: marked.Mark

  def __init__(self, name: marked.MarkedTuple[str], arg: elements.Argument | None):
    super().__init__(f'--{name[1]}')
    self.__name = marked.Marked(name)
    self.arg = arg
    self.mark = marked.Mark(self.__name.start, self.arg.mark.end if self.arg else self.__name.end)

  @property
  def name(self):
    return self.__name.elm

  def __repr__(self):
    return f'''--{self.name}{self.repeatable_suffix}
  arg: {self.arg}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'name', self.name
    yield 'repeatable', self.repeatable
    yield 'arg', dict(self.arg) if self.arg else None
