import re
from parsec import regex, many1  # type: ignore

from docopt_parser import base, helpers, parsers, marked

other_documentation = many1(parsers.char(illegal=regex(r'[^\n]*(options:|usage:)', re.I))) \
  .mark().desc('Text').parsecmap(helpers.join_string).parsecmap(lambda n: Text(n))

class Text(base.AstLeaf):
  __text: marked.Marked[str]
  mark: marked.Mark

  def __init__(self, text: marked.MarkedTuple[str]):
    super().__init__()
    self.__text = marked.Marked(text)
    self.mark = marked.Mark(self.__text.start, self.__text.end)

  def __repr__(self):
    return '<Text>'

  def __iter__(self) -> base.DictGenerator:
    yield '--'
