from docopt_parser import base
from docopt_parser.util import marks, parsers

class Command(base.Leaf):
  def __init__(self, name: marks.MarkedTuple[str]):
    super().__init__(name)

command = base.ident(
  parsers.non_symbol_chars, starts_with=parsers.char(illegal=parsers.non_symbol_chars)
).mark().parsecmap(lambda n: Command(n))
