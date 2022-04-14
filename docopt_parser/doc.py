from typing import Iterable, List, Tuple, cast
from parsec import ParseError, many, generate
from ordered_set import OrderedSet

from docopt_parser import base, sections, elements, helpers, marked


def doc(strict: bool):
  @generate('docopt')
  def p() -> helpers.GeneratorParser[Doc]:
    items: Tuple[
      Tuple[
        List[sections.OptionsSection | elements.Text],
        sections.UsageSection
      ],
      List[sections.OptionsSection | elements.Text]
    ] = yield (
      many(sections.options_section(strict) | elements.other_documentation)
      + sections.usage_section(strict)
      + many(sections.options_section(strict) | elements.other_documentation)
    )
    ((pre, usage), post) = items
    option_sections = list(n for n in pre + post if isinstance(n, sections.OptionsSection))
    return Doc(usage, option_sections)
  return p

class Doc(base.AstNode):
  usage_section: sections.UsageSection
  option_sections: Iterable[sections.OptionsSection]

  def __init__(self, usage_section: sections.UsageSection, option_sections: List[sections.OptionsSection]):
    super().__init__(cast(List[base.AstLeaf], [usage_section]) + cast(List[base.AstLeaf], option_sections))
    self.usage_section = usage_section
    self.option_sections = option_sections

  @property
  def usage_options(self) -> OrderedSet[elements.DocumentedOption]:
    def get_opts(memo: OrderedSet[elements.DocumentedOption], node: base.AstLeaf):
      if isinstance(node, elements.DocumentedOption):
        memo.add(node)
      return memo
    return self.usage_section.reduce(get_opts, OrderedSet[elements.DocumentedOption]([]))

  @property
  def section_options(self) -> OrderedSet[elements.DocumentedOption]:
    return OrderedSet(sum([o.items for o in self.option_sections], []))

  def __repr__(self) -> str:
    return f'''{self.indent(self.items, lvl=0)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'usage', dict(self.usage_section)
    yield 'options', [dict(option) for option in self.option_sections]


def parse(txt: str, strict: bool = True) -> Tuple[Doc, str]:
  from docopt_parser import post_processors
  try:
    parser = doc(strict)
    if strict:
      ast = parser.parse_strict(txt)
      parsed_doc = txt
    else:
      ast, parsed_doc = parser.parse_partial(txt)
    ast = post_processors.post_process_ast(ast, txt)
    # TODO: Mark multi elements as such
    return ast, parsed_doc
  except ParseError as e:
    raise DocoptParseError(marked.explain_error(e, txt)) from e

class DocoptParseError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__()
    self.message = message
    self.exit_code = exit_code
