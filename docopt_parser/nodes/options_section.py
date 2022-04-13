import re
from typing import Generator, Iterator, Union
from parsec import Parser, eof, generate, many, many1, optional, regex
from . import char, eol, fail_with, indent, join_string, lookahead, nl, whitespaces, string
from .astnode import AstNode
from .option import Option
from .argument import argument
from .short import Short, illegal as short_illegal
from .long import Long, illegal as long_illegal
from .identnode import ident

next_option = nl + optional(indent) + char('-')
terminator = (nl + nl) ^ (nl + eof()) ^ next_option
default = (
  regex(r'\[default: ', re.IGNORECASE) >> many(char(illegal='\n]')) << char(']')
).desc('[default: ]').parsecmap(join_string)
doc = many1(char(illegal=default ^ terminator)).desc('option documentation').parsecmap(join_string)

def section(strict):
  @generate('options section')
  def p() -> Generator[Parser, Parser, OptionsSection]:
    options = []
    title = yield regex(r'[^\n]*options:', re.I)
    yield nl + optional(indent)
    while (yield lookahead(optional(char('-')))) is not None:
      doc1 = _default = doc2 = None
      (short, long) = yield option_line_opts
      if (yield optional(lookahead(eol))) is not None:
        # Consume trailing whitespaces
        yield whitespaces
      elif (yield optional(lookahead(char(illegal='\n')))) is not None:
        yield (char(' ') + many1(char(' '))) ^ fail_with('at least 2 spaces')
        doc1 = yield optional(doc)
        _default = yield optional(default)
        doc2 = yield optional(doc)
      options.append(Option(short, long, True, doc1, _default, doc2))
      if (yield lookahead(optional(next_option))) is None:
        break
      yield nl + optional(indent)
    if strict:
      yield eof() | nl
    else:
      # Do not enforce section termination when parsing non-strictly
      yield optional(eof() | nl)
    return OptionsSection(title, options)
  return p

class OptionsSection(AstNode):
  title: str
  items: list[Option]

  def __init__(self, title: str, items: list[Option]):
    self.title = title
    super().__init__(items)

  def __repr__(self) -> str:
    return f'''<OptionsSection> {self.title}
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, list[dict]]]]:
    yield 'title', self.title
    yield 'items', list(map(dict, self.items))

@generate('short option (-s)')
def option_line_short() -> Generator[Parser, Parser, Short]:
  argspec = (char(' =') >> argument).desc('argument')
  yield char('-')
  name = yield char(illegal=short_illegal)
  if (yield optional(lookahead(char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return Short(name, arg)

@generate('long option (--long)')
def option_line_long() -> Generator[Parser, Parser, Long]:
  argspec = (char(' =') >> argument).desc('argument')
  yield string('--')
  name = yield ident(long_illegal)
  if (yield optional(lookahead(char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield optional(argspec)
  return Long(name, arg)

@generate('options')
def option_line_opts() -> Generator[Parser, Parser, Union[tuple[Short, Long], tuple[Short, None], tuple[None, Long]]]:
  first = yield option_line_long | option_line_short
  if isinstance(first, Long):
    opt_short = yield optional((string(', ') | char(' ')) >> option_line_short)
    opt_long = first
  else:
    opt_short = first
    opt_long = yield optional((string(', ') | char(' ')) >> option_line_long)
  if opt_short is not None and opt_long is not None:
    if opt_short.arg is not None and opt_long.arg is None:
      opt_long.arg = opt_short.arg
    if opt_short.arg is None and opt_long.arg is not None:
      opt_short.arg = opt_long.arg
  return (opt_short, opt_long)
