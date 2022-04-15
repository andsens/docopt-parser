from typing import Dict, Iterable, List, Tuple, cast
from parsec import ParseError, many, generate

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
    text = list(n for n in pre + post if isinstance(n, elements.Text))
    return Doc(usage, option_sections, text)
  return p

class Doc(base.AstNode):
  usage_section: sections.UsageSection
  option_sections: Iterable[sections.OptionsSection]
  text: Iterable[elements.Text]

  def __init__(
    self,
    usage_section: sections.UsageSection,
    option_sections: List[sections.OptionsSection],
    text: List[elements.Text]
  ):
    super().__init__(cast(List[base.AstLeaf], [usage_section]) + cast(List[base.AstLeaf], option_sections))
    self.usage_section = usage_section
    self.option_sections = option_sections
    self.text = text

  @property
  def usage_options(self) -> List[elements.Short | elements.Long]:
    def get_opts(memo: List[elements.Short | elements.Long], node: base.AstLeaf):
      if isinstance(node, elements.Short | elements.Long):
        memo.append(node)
      return memo
    return self.usage_section.reduce(get_opts, [])

  @property
  def section_options(self) -> List[elements.DocumentedOption]:
    return sum([o.items for o in self.option_sections], [])

  def get_option_definition(
    self, needle: elements.Short | elements.Long) -> elements.Short | elements.Long | elements.DocumentedOption:
    for option in self.section_options:
      if isinstance(needle, elements.Short) and option.short is not None and option.short.ident == needle.ident:
        return option
      if isinstance(needle, elements.Long) and option.long is not None and option.long.ident == needle.ident:
        return option
    for option in self.usage_options:
      if option.ident == needle.ident:
        return option
    raise DocoptError(f'Unable to find option: {needle}')

  @property
  def grouped_options(self) -> Dict[str, Tuple[elements.DocumentedOption | None, List[elements.Short | elements.Long]]]:
    aliases: Dict[str, elements.DocumentedOption] = {}
    grouped: Dict[str, Tuple[elements.DocumentedOption | None, List[elements.Short | elements.Long]]] = {}
    for option in self.section_options:
      if option.long is not None and option.short is not None:
        aliases[option.short.ident] = option
      grouped[option.ident] = (option, [])
    for opt in self.usage_options:
      ident = opt.ident
      if isinstance(opt, elements.Short) and aliases.get(ident, None) is not None:
        ident = aliases[ident].ident
      if grouped.get(ident, None) is None:
        grouped[opt.ident] = (None, [])
      grouped[opt.ident][1].append(opt)
    return grouped

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
    return ast, parsed_doc
  except ParseError as e:
    raise DocoptParseError(marked.explain_error(e, txt)) from e

class DocoptError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__(message)
    self.message = message
    self.exit_code = exit_code

class DocoptParseError(DocoptError):
  pass
