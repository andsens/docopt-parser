from typing import Generator, Iterator, Union
from parsec import Parser, ParseError, regex, many, many1, generate
from ordered_set import OrderedSet
import re

from docopt_parser import base, sections, elements, parsers, helpers, marked

other_documentation = many1(parsers.char(illegal=regex(r'[^\n]*(options:|usage:)', re.I))) \
  .desc('Text').parsecmap(helpers.join_string)

def doc(strict: bool):
  @generate('docopt')
  def p() -> Generator[Parser, Parser, Doc]:
    items = list(filter(lambda part: part != [], (yield (
      many(sections.options_section(strict) | other_documentation)
      + sections.usage_section(strict)
      + many(sections.options_section(strict) | other_documentation)
    ).parsecmap(helpers.flatten))))
    return Doc(items)
  return p

class Doc(base.AstNode):
  usage: sections.UsageSection
  option_sections: list[sections.OptionsSection]

  def __init__(self, items: list[sections.UsageSection, sections.OptionsSection, str]):
    super().__init__(items)
    self.usage = next(filter(lambda n: isinstance(n, sections.UsageSection), self.items), None)
    self.option_sections = list(filter(lambda n: isinstance(n, sections.OptionsSection), self.items))

  @property
  def usage_options(self) -> list[elements.DocumentedOption]:
    def get_opts(memo, node):
      if isinstance(node, elements.DocumentedOption):
        memo.add(node)
      return memo
    return self.usage.reduce(get_opts, OrderedSet())

  @property
  def section_options(self) -> list[elements.DocumentedOption]:
    return OrderedSet(sum([o.items for o in self.option_sections], []))

  def __repr__(self) -> str:
    return f'''{self.indent(self.items, lvl=0)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, list[dict]]]]:
    yield 'usage', dict(self.usage)
    yield 'options', list(map(dict, self.option_sections))


def parse(txt: str, strict: bool = True) -> Doc:
  from docopt_parser import post_processors
  try:
    parser = doc(strict)
    if strict:
      ast = parser.parse_strict(txt)
    else:
      ast = parser.parse_partial(txt)
    post_processors.post_process_ast(ast, txt)
    # TODO: Mark multi elements as such
    return ast
  except ParseError as e:
    raise DocoptParseError(marked.explain_error(e, txt)) from e

class DocoptParseError(Exception):
  def __init__(self, message: str, exit_code=1):
    self.message = message
    self.exit_code = exit_code
