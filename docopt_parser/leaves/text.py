import re
import parsec as P

from docopt_parser import base, helpers, marks, parsers

other_documentation = P.many1(parsers.char(
  illegal=P.regex(r'[^\n]*(options:|usage:)', re.I))  # type: ignore
  ).desc('Text').parsecmap(helpers.join_string).mark().parsecmap(lambda n: Text(n))

class Text(base.AstElement):
  text: str

  def __init__(self, text: marks.MarkedTuple[str]):
    super().__init__((text[0], text[2]))
    self.text = text[1]

  def __repr__(self):
    return '<Text>'

  def __iter__(self):
    yield from super().__iter__()
    yield 'text', self.text
