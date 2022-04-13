from typing import Generator, Iterator, Union

from parsec import Parser, regex, many, many1, generate
from . import char, join_string, flatten
import re
from .astnode import AstNode
from .options_section import OptionsSection, section as options_section
from .usage_section import UsageSection, section as usage_section
from .option import Option
from .optionref import OptionRef
from ordered_set import OrderedSet

other_documentation = many1(char(illegal=regex(r'[^\n]*(options:|usage:)', re.I))).desc('Text').parsecmap(join_string)

def doc(strict: bool):
  @generate('docopt')
  def p() -> Generator[Parser, Parser, Doc]:
    items = list(filter(lambda part: part != [], (yield (
      many(options_section(strict) | other_documentation)
      + usage_section(strict)
      + many(options_section(strict) | other_documentation)
    ).parsecmap(flatten))))
    return Doc(items)
  return p

class Doc(AstNode):
  usage: UsageSection
  option_sections: list[OptionsSection]

  def __init__(self, items: list[UsageSection, OptionsSection, str]):
    super().__init__(items)
    self.usage = next(filter(lambda n: isinstance(n, UsageSection), self.items), None)
    self.option_sections = list(filter(lambda n: isinstance(n, OptionsSection), self.items))

  @property
  def usage_options(self) -> list[Option]:
    def get_opts(memo, node):
      if isinstance(node, Option):
        memo.add(node)
      if isinstance(node, OptionRef):
        memo.add(node.ref)
      return memo
    return self.usage.reduce(get_opts, OrderedSet())

  @property
  def section_options(self) -> list[Option]:
    return OrderedSet(sum([o.items for o in self.option_sections], []))

  def __repr__(self) -> str:
    return f'''{self.indent(self.items, lvl=0)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, list[dict]]]]:
    yield 'usage', dict(self.usage)
    yield 'options', list(map(dict, self.option_sections))
