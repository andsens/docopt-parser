import re
import typing as T
import parsec as P

from docopt_parser import base, elements, parsers, helpers, marked
from docopt_parser.elements.documented_option import DocumentedOption

next_option = parsers.nl + P.optional(parsers.indent) + parsers.char('-')
terminator = (parsers.nl + parsers.nl) ^ (parsers.nl + P.eof()) ^ next_option
default = (
  P.regex(r'\[default: ', re.IGNORECASE) >> P.many(parsers.char(illegal='\n]')) << parsers.char(']')  # type: ignore
).desc('[default: ]').parsecmap(helpers.join_string)
doc = P.many1(parsers.char(illegal=default ^ terminator)).desc('option documentation').parsecmap(helpers.join_string)

def options_section(strict: bool):
  @P.generate('options section')
  def p() -> helpers.GeneratorParser[OptionsSection]:
    options: T.Sequence[DocumentedOption] = []
    title = yield P.regex(r'[^\n]*options:', re.I).mark()  # type: ignore
    yield parsers.nl + P.optional(parsers.indent)
    while (yield P.lookahead(P.optional(parsers.char('-')))) is not None:
      _doc = _default = None
      (short, long) = yield option_line_opts
      if (yield P.optional(P.lookahead(parsers.eol))) is not None:
        # Consume trailing whitespaces
        yield parsers.whitespaces
      elif (yield P.optional(P.lookahead(parsers.char(illegal='\n')))) is not None:
        yield (parsers.char(' ') + P.many1(parsers.char(' '))) ^ P.fail_with('at least 2 spaces')  # type: ignore
        _default = yield P.lookahead(P.optional(doc) >> P.optional(default).mark() << P.optional(doc))
        _doc = yield P.optional(doc).mark()
      options.append(elements.DocumentedOption(short, long, _default, _doc))
      if (yield P.lookahead(P.optional(next_option))) is None:
        break
      yield parsers.nl + P.optional(parsers.indent)
    if strict:
      yield P.eof() | parsers.nl
    else:
      # Do not enforce section termination when parsing non-strictly
      yield P.optional(P.eof() | parsers.nl)
    return OptionsSection(title, options)
  return p

class OptionsSection(base.AstNode):
  __title: marked.Marked[str]
  items: T.List[elements.DocumentedOption]
  mark: marked.Mark

  def __init__(self, __title: marked.MarkedTuple[str], items: T.Sequence[elements.DocumentedOption]):
    super().__init__(items)
    self.__title = marked.Marked(__title)
    self.mark = marked.Mark(self.__title.start, max([e.mark.end for e in self.items]))

  @property
  def title(self) -> str:
    return self.__title.elm

  def __repr__(self) -> str:
    return f'''<OptionsSection> {self.title}
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'title', self.title
    yield 'items', [dict(item) for item in self.items]

@P.generate('short option (-s)')
def option_line_short() -> helpers.GeneratorParser[elements.Short]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.char('-') >> parsers.char(illegal=elements.short_illegal)).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return elements.Short(name, arg)

@P.generate('long option (--long)')
def option_line_long() -> helpers.GeneratorParser[elements.Long]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.string('--') >> base.ident(elements.long_illegal)).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return elements.Long(name, arg)

@P.generate('options')
def option_line_opts() -> helpers.GeneratorParser[
  T.Tuple[elements.Short, elements.Long]
  | T.Tuple[elements.Short, None]
  | T.Tuple[None, elements.Long]
]:
  first = yield option_line_long | option_line_short
  if isinstance(first, elements.Long):
    opt_short = yield P.optional((parsers.string(', ') | parsers.char(' ')) >> option_line_short)
    opt_long = first
  else:
    opt_short = first
    opt_long = yield P.optional((parsers.string(', ') | parsers.char(' ')) >> option_line_long)
  if opt_short is not None and opt_long is not None:
    if opt_short.arg is not None and opt_long.arg is None:
      opt_long.arg = opt_short.arg
    if opt_short.arg is None and opt_long.arg is not None:
      opt_short.arg = opt_long.arg
  return (opt_short, opt_long)
