from docopt_parser import base
from docopt_parser.util import marks, parsers

illegal = parsers.non_symbol_chars

class Command(base.Leaf):
  def __init__(self, name: marks.MarkedTuple[str]):
    super().__init__(name)

command = base.ident(illegal, starts_with=parsers.char(illegal=illegal | parsers.char('-'))).mark() \
  .parsecmap(lambda n: Command(n))
