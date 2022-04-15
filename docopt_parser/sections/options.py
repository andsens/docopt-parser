import re
from typing import Iterable, List, Tuple
from parsec import eof, generate, many, many1, optional, regex, lookahead, fail_with  # type: ignore

from docopt_parser import base, elements, parsers, helpers, marked
from docopt_parser.elements.documented_option import DocumentedOption

next_option = parsers.nl + optional(parsers.indent) + parsers.char('-')
terminator = (parsers.nl + parsers.nl) ^ (parsers.nl + eof()) ^ next_option
default = (
  regex(r'\[default: ', re.IGNORECASE) >> many(parsers.char(illegal='\n]')) << parsers.char(']')
).desc('[default: ]').parsecmap(helpers.join_string)
doc = many1(parsers.char(illegal=default ^ terminator)).desc('option documentation').parsecmap(helpers.join_string)

def options_section(strict: bool):
  @generate('options section')
  def p() -> helpers.GeneratorParser[OptionsSection]:
    options: List[DocumentedOption] = []
    title = yield regex(r'[^\n]*options:', re.I).mark()
    yield parsers.nl + optional(parsers.indent)
    while (yield lookahead(optional(parsers.char('-')))) is not None:
      _doc = _default = None
      (short, long) = yield option_line_opts
      if (yield optional(lookahead(parsers.eol))) is not None:
        # Consume trailing whitespaces
        yield parsers.whitespaces
      elif (yield optional(lookahead(parsers.char(illegal='\n')))) is not None:
        yield (parsers.char(' ') + many1(parsers.char(' '))) ^ fail_with('at least 2 spaces')
        _default = yield lookahead(optional(doc) >> optional(default).mark() << optional(doc))
        _doc = yield optional(doc).mark()
      options.append(elements.DocumentedOption(short, long, _default, _doc))
      if (yield lookahead(optional(next_option))) is None:
        break
      yield parsers.nl + optional(parsers.indent)
    if strict:
      yield eof() | parsers.nl
    else:
      # Do not enforce section termination when parsing non-strictly
      yield optional(eof() | parsers.nl)
    return OptionsSection(title, options)
  return p

class OptionsSection(base.AstNode):
  __title: marked.Marked[str]
  items: List[elements.DocumentedOption]
  mark: marked.Mark

  def __init__(self, __title: marked.MarkedTuple[str], items: Iterable[elements.DocumentedOption]):
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

@generate('short option (-s)')
def option_line_short() -> helpers.GeneratorParser[elements.Short]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.char('-') >> parsers.char(illegal=elements.short_illegal)).mark()
  if (yield optional(lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return elements.Short(name, arg)

@generate('long option (--long)')
def option_line_long() -> helpers.GeneratorParser[elements.Long]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.string('--') >> base.ident(elements.long_illegal)).mark()
  if (yield optional(lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return elements.Long(name, arg)

@generate('options')
def option_line_opts() -> helpers.GeneratorParser[
  Tuple[elements.Short, elements.Long]
  | Tuple[elements.Short, None]
  | Tuple[None, elements.Long]
]:
  first = yield option_line_long | option_line_short
  if isinstance(first, elements.Long):
    opt_short = yield optional((parsers.string(', ') | parsers.char(' ')) >> option_line_short)
    opt_long = first
  else:
    opt_short = first
    opt_long = yield optional((parsers.string(', ') | parsers.char(' ')) >> option_line_long)
  if opt_short is not None and opt_long is not None:
    if opt_short.arg is not None and opt_long.arg is None:
      opt_long.arg = opt_short.arg
    if opt_short.arg is None and opt_long.arg is not None:
      opt_short.arg = opt_long.arg
  return (opt_short, opt_long)
