import typing as T
import parsec as P

from docopt_parser import base, groups, marks, sections, leaves, helpers, parsers


def doc(strict: bool):
  @P.generate('docopt')
  def p() -> helpers.GeneratorParser[Doc]:
    start = yield parsers.location
    items: T.Tuple[
      T.Tuple[
        T.List[sections.OptionsSection | leaves.Text],
        T.Tuple[str, groups.Choice | groups.Sequence]
      ],
      T.List[sections.OptionsSection | leaves.Text]
    ] = yield (
      P.many(sections.options_section(strict) | leaves.other_documentation)
      + sections.usage_section(strict)
      + P.many(sections.options_section(strict) | leaves.other_documentation)
    )
    end = yield parsers.location
    ((pre, (prog, usage)), post) = items
    option_sections = list(n for n in pre + post if isinstance(n, sections.OptionsSection))
    text = list(n for n in pre + post if isinstance(n, leaves.Text))
    return Doc((start, end), prog, usage, option_sections, text)
  return p

class Doc(base.AstElement):
  prog: str
  usage: groups.Choice | groups.Sequence
  option_sections: T.List[sections.OptionsSection]
  text: T.List[leaves.Text]

  def __init__(
    self,
    range: marks.RangeTuple,
    prog: str,
    usage: groups.Choice | groups.Sequence,
    option_sections: T.Sequence[sections.OptionsSection],
    text: T.Sequence[leaves.Text]
  ):
    super().__init__(range)
    self.prog = prog
    self.usage = usage
    self.option_sections = list(option_sections)
    self.text = list(text)

  @property
  def usage_options(self) -> T.List[leaves.Short | leaves.Long]:
    def get_opts(memo: T.List[leaves.Short | leaves.Long], node: base.AstNode):
      if isinstance(node, leaves.Short | leaves.Long):
        memo.append(node)
      return memo
    return self.usage.reduce(get_opts, [])

  @property
  def section_options(self) -> T.List[leaves.DocumentedOption]:
    return sum([o.items for o in self.option_sections], [])

  def get_option_definition(
    self, needle: leaves.Short | leaves.Long) -> leaves.Short | leaves.Long | leaves.DocumentedOption:
    for option in self.section_options:
      if isinstance(needle, leaves.Short) and option.short is not None and option.short.ident == needle.ident:
        return option
      if isinstance(needle, leaves.Long) and option.long is not None and option.long.ident == needle.ident:
        return option
    for option in self.usage_options:
      if option.ident == needle.ident:
        return option
    raise DocoptError(f'Unable to find option: {needle}')

  def __repr__(self) -> str:
    items = T.cast(T.List[base.AstNode], [self.usage]) + T.cast(T.List[base.AstNode], self.option_sections)
    return f'''{self.indent(items, lvl=0)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', str(type(self).__name__).lower()
    yield 'usage', dict(self.usage)
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
    raise DocoptParseError(marks.explain_error(e, txt)) from e

class DocoptError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__(message)
    self.message = message
    self.exit_code = exit_code

class DocoptParseError(DocoptError):
  pass
