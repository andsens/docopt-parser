import parsec as P

from docopt_parser import base, marks, parsers

arg_separator = P.unit(parsers.string('--') << P.lookahead(parsers.non_symbol_chars)).mark() \
  .parsecmap(lambda n: ArgumentSeparator(n))

class ArgumentSeparator(base.AstLeaf):
  def __init__(self, text: marks.MarkedTuple[str]):
    super().__init__((text[0], text[2]))

  def __repr__(self):
    return f'<ArgumentSeparator{self.multiple_suffix}>{self.repeatable_suffix}'

  def __iter__(self):
    yield from super().__iter__()
