from docopt_parser import base, marks, parsers

class Repeatable(base.AstNode):
  def __init__(self, text: marks.MarkedTuple[str]):
    super().__init__((text[0], text[2]))

  def __repr__(self):
    return '<Repeatable>'

repeatable = parsers.ellipsis.mark().parsecmap(lambda n: Repeatable(n))
