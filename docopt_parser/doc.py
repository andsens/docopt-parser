import typing as T
import parsec as P

from docopt_parser import base, sections, elements, helpers, marked


def doc(strict: bool):
  @P.generate('docopt')
  def p() -> helpers.GeneratorParser[Doc]:
    items: T.Tuple[
      T.Tuple[
        T.List[sections.OptionsSection | elements.Text],
        sections.UsageSection
      ],
      T.List[sections.OptionsSection | elements.Text]
    ] = yield (
      P.many(sections.options_section(strict) | elements.other_documentation)
      + sections.usage_section(strict)
      + P.many(sections.options_section(strict) | elements.other_documentation)
    )
    ((pre, usage), post) = items
    option_sections = list(n for n in pre + post if isinstance(n, sections.OptionsSection))
    text = list(n for n in pre + post if isinstance(n, elements.Text))
    return Doc(usage, option_sections, text)
  return p

class Doc(base.AstNode):
  usage_section: sections.UsageSection
  option_sections: T.List[sections.OptionsSection]
  text: T.List[elements.Text]

  def __init__(
    self,
    usage_section: sections.UsageSection,
    option_sections: T.Sequence[sections.OptionsSection],
    text: T.Sequence[elements.Text]
  ):
    self.usage_section = usage_section
    self.option_sections = list(option_sections)
    self.text = list(text)
    super().__init__(T.cast(T.List[base.AstLeaf], [usage_section]) + T.cast(T.List[base.AstLeaf], option_sections))

  @property
  def usage_options(self) -> T.List[elements.Short | elements.Long]:
    def get_opts(memo: T.List[elements.Short | elements.Long], node: base.AstLeaf):
      if isinstance(node, elements.Short | elements.Long):
        memo.append(node)
      return memo
    return self.usage_section.reduce(get_opts, [])

  @property
  def section_options(self) -> T.List[elements.DocumentedOption]:
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
  def grouped_options(self) -> T.Dict[
    str,
    T.Tuple[elements.DocumentedOption | None, T.List[elements.Short | elements.Long]]
  ]:
    aliases: T.Dict[str, elements.DocumentedOption] = {}
    grouped: T.Dict[str, T.Tuple[elements.DocumentedOption | None, T.List[elements.Short | elements.Long]]] = {}
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


def parse(txt: str, strict: bool = True) -> T.Tuple[Doc, str]:
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
  except P.ParseError as e:
    raise DocoptParseError(marked.explain_error(e, txt)) from e

class DocoptError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__(message)
    self.message = message
    self.exit_code = exit_code

class DocoptParseError(DocoptError):
  pass
