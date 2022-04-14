import re
from typing import Generator, Iterator, Union
from parsec import Parser, eof, generate, many, many1, optional, regex, lookahead, fail_with

from docopt_parser import base, elements, parsers, helpers, marked

next_option = parsers.nl + optional(parsers.indent) + parsers.char('-')
terminator = (parsers.nl + parsers.nl) ^ (parsers.nl + eof()) ^ next_option
default = (
  regex(r'\[default: ', re.IGNORECASE) >> many(parsers.char(illegal='\n]')) << parsers.char(']')
).desc('[default: ]').parsecmap(helpers.join_string)
doc = many1(parsers.char(illegal=default ^ terminator)).desc('option documentation').parsecmap(helpers.join_string)

def options_section(strict):
  @generate('options section')
  def p() -> Generator[Parser, Parser, OptionsSection]:
    options = []
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
      options.append(elements.DocumentedOption(short, long, True, _default, _doc))
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
  __title: marked.Marked
  items: list[elements.DocumentedOption]
  mark: marked.Mark

  def __init__(self, __title: marked.MarkedTuple, items: list[elements.DocumentedOption]):
    super().__init__(items)
    self.__title = marked.Marked(__title)
    self.mark = marked.Mark(self.__title.start, max([e.mark.end for e in self.items]))

  @property
  def title(self) -> str:
    return self.__title.txt

  def __repr__(self) -> str:
    return f'''<OptionsSection> {self.title}
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, list[dict]]]]:
    yield 'title', self.title
    yield 'items', list(map(dict, self.items))

@generate('short option (-s)')
def option_line_short() -> Generator[Parser, Parser, elements.Short]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.char('-') >> parsers.char(illegal=elements.short_illegal)).mark()
  if (yield optional(lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return elements.Short(name, arg)

@generate('long option (--long)')
def option_line_long() -> Generator[Parser, Parser, elements.Long]:
  argspec = (parsers.char(' =') >> elements.argument).desc('argument')
  name = yield (parsers.string('--') >> base.ident(elements.long_illegal)).mark()
  if (yield optional(lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return elements.Long(name, arg)

@generate('options')
def option_line_opts() -> Generator[Parser, Parser, Union[
  tuple[elements.Short, elements.Long], tuple[elements.Short, None], tuple[None, elements.Long]
]]:
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
