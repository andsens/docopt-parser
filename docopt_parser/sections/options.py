import re
import typing as T
import parsec as P

from docopt_parser import base, leaves, marks, parsers, helpers


def options_section(strict: bool):
  @P.generate('options section')
  def p() -> helpers.GeneratorParser[OptionsSection]:
    options: T.Sequence[leaves.DocumentedOption] = []
    start = yield parsers.location
    title = yield P.regex(r'[^\n]*options:', re.I).mark()  # type: ignore
    yield parsers.nl + P.optional(parsers.indent)
    while (yield P.lookahead(P.optional(parsers.char('-')))) is not None:
      options.append((yield leaves.documented_option))
      if (yield P.lookahead(P.optional(leaves.next_documented_option))) is None:
        break
      yield parsers.nl + P.optional(parsers.indent)
    if strict:
      yield P.eof() | parsers.nl
    else:
      # Do not enforce section termination when parsing non-strictly
      yield P.optional(P.eof() | parsers.nl)
    end = yield parsers.location
    return OptionsSection((start, options, end), title)
  return p

class OptionsSection(base.AstGroup):
  items: T.List[leaves.DocumentedOption]
  __title: marks.Marked[str]

  def __init__(self, items: marks.MarkedTuple[T.Sequence[leaves.DocumentedOption]], __title: marks.MarkedTuple[str]):
    super().__init__(items)
    self.__title = marks.Marked(__title)

  @property
  def title(self) -> str:
    return self.__title.elm

  def __repr__(self) -> str:
    return f'''<OptionsSection> {self.title}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    super().__iter__()
    yield 'title', self.title
