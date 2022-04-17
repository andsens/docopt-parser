import typing as T
import typing_extensions as TE
import parsec as P

from docopt_parser import base, groups, marks, sections, leaves, helpers, parsers

AnyOption = T.Union[leaves.Short, leaves.Long, leaves.DocumentedOption, leaves.OptionRef]

def doc(strict: bool):
  @P.generate('docopt')
  def p() -> helpers.GeneratorParser[Doc]:
    usage_section = sections.usage_section(strict)
    options_section = sections.options_section(strict)
    prog: str | None = None
    usage: base.Group | None = None
    option_sections: T.List[sections.OptionsSection] = []
    text: T.List[leaves.Text] = []
    current: T.Tuple[str, base.Group] | sections.OptionsSection | leaves.Text
    start = yield parsers.location
    # We don't use the many parser here, since any errors would be swallowed by it
    # (same as in the groups parsers)
    while (yield P.optional(P.eof().result(True))) is None:
      current = yield usage_section | options_section | leaves.other_documentation
      if isinstance(current, sections.OptionsSection):
        option_sections.append(current)
      elif isinstance(current, leaves.Text):
        text.append(current)
      else:
        if prog is not None:
          raise DocoptParseError('Unexpected additional Usage:', current[1].mark)
        prog, usage = current
    if prog is None or usage is None:
      raise DocoptParseError('Expected "Usage:"')
    end = yield parsers.location
    return Doc((start, end), prog, usage, option_sections, text)
  return p

class Doc(base.Node):
  prog: str
  _usage: base.Group
  option_sections: T.List[sections.OptionsSection]
  text: T.List[leaves.Text]

  def __init__(
    self,
    range: marks.RangeTuple,
    prog: str,
    usage: base.Group,
    option_sections: T.Sequence[sections.OptionsSection],
    text: T.Sequence[leaves.Text]
  ):
    super().__init__(range)
    self.prog = prog
    self._usage = usage
    self.option_sections = list(option_sections)
    self.text = list(text)

  @property
  def usage(self) -> base.Group:
    return self._usage

  @usage.setter
  def usage(self, usage: "base.Node | None"):  # type: ignore
    # Ignoring because the type incompatibility is the point here
    if usage is None:
      items: T.List[base.Node] = []
      self._usage = groups.Sequence(self._usage.mark.wrap_element(items).to_marked_tuple())
    elif not isinstance(usage, base.Group):
      self._usage = groups.Sequence(self._usage.mark.wrap_element([usage]).to_marked_tuple())
    else:
      self._usage = usage

  @property
  def usage_options(self) -> T.List[AnyOption]:
    def get_opts(memo: T.List[AnyOption], node: base.Node):
      if isinstance(node, (leaves.Short, leaves.Long, leaves.DocumentedOption, leaves.OptionRef)):
        memo.append(node)
      return memo
    return self._usage.reduce(get_opts, [])

  @property
  def section_options(self) -> T.List[leaves.DocumentedOption]:
    return sum([list(o.items) for o in self.option_sections], [])

  def get_option_definition(
    self, needle: "leaves.Short | leaves.Long") -> "leaves.Short | leaves.Long | leaves.DocumentedOption":
    for option in self.section_options:
      if option == needle or (option.short is not None and option.short.ident == needle.ident):
        return option
    for option in self.usage_options:
      if not isinstance(option, leaves.OptionRef) and option.ident == needle.ident:
        return option
    raise DocoptError(f'Unable to find option: {needle}')

  def __repr__(self) -> str:
    items = T.cast(T.List[base.Node], [self._usage]) + T.cast(T.List[base.Node], self.option_sections)
    return f'''{self.indent(items, lvl=0)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', str(type(self).__name__).lower()
    yield 'usage', self._usage.dict
    yield 'options', [option.dict for option in self.option_sections]

@T.overload
def parse(text: str, strict: TE.Literal[False]) -> T.Tuple[Doc, str]:
  pass

@T.overload
def parse(text: str, strict: TE.Literal[True] = True) -> T.Tuple[base.Group, str]:
  pass

def parse(text: str, strict: bool = True) -> "T.Tuple[base.Group | Doc, str]":
  from docopt_parser import post_processors
  try:
    parser = doc(strict)
    if strict:
      ast = parser.parse_strict(text)
      parsed_doc = text
    else:
      ast, parsed_doc = parser.parse_partial(text)
    ast = post_processors.post_process_ast(ast, text)
    if strict:
      return ast.usage, parsed_doc
    else:
      return ast, parsed_doc
  except DocoptParseError as e:
    if e.mark is not None:
      raise DocoptError(e.mark.show(text, e.message), e.exit_code) from e
    else:
      raise DocoptError(e.message, e.exit_code) from e
  except P.ParseError as e:
    loc = marks.Location(e.loc_info(e.text, e.index))
    raise DocoptError(loc.show(text, str(e))) from e

class DocoptError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__(message)
    self.message = message
    self.exit_code = exit_code

class DocoptParseError(DocoptError):
  mark: "marks.Location | marks.Range | None"

  def __init__(self, message: str, mark: "marks.Location | marks.Range | None" = None):
    super().__init__(message, 1)
    self.mark = mark
