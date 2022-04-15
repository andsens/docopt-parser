import re
from parsec import regex, many1  # type: ignore

from docopt_parser import base, helpers, parsers, marked

other_documentation = many1(parsers.char(illegal=regex(r'[^\n]*(options:|usage:)', re.I))) \
  .desc('Text').parsecmap(helpers.join_string).mark().parsecmap(lambda n: Text(n))

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
