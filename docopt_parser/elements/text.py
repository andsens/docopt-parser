import re
import parsec as P

from docopt_parser import base, helpers, parsers, marked

other_documentation = P.many1(parsers.char(
  illegal=P.regex(r'[^\n]*(options:|usage:)', re.I))  # type: ignore
  ).desc('Text').parsecmap(helpers.join_string).mark().parsecmap(lambda n: Text(n))

class Text(base.AstLeaf):
  __text: marked.Marked[str]

  def __init__(self, text: marked.MarkedTuple[str]):
    super().__init__()
    self.__text = marked.Marked(text)

  @property
  def mark(self) -> marked.Mark:
    return self.__text

  def __repr__(self):
    return '<Text>'

  def __iter__(self) -> base.DictGenerator:
    yield 'text', self.__text.elm
