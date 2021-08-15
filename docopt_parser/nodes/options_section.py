import re
from parsec import eof, generate, many, many1, optional, regex
from . import char, eol, fail_with, indent, join_string, lookahead, nl, whitespaces, string
from .option import Option
from .argument import argument
from .short import Short, illegal as short_illegal
from .long import Long, illegal as long_illegal
from .identnode import ident

re_options_section = regex(r'options:', re.I)
no_options_text = many(char(illegal=re_options_section)).desc('Text').parsecmap(join_string)
def options_sections(strict=True):
  @generate('options: sections')
  def p():
    options = []
    while True:
      yield no_options_text
      if (yield lookahead(optional(re_options_section))) is None:
        break
      options.extend((yield section(strict)))
    validate_unambiguous_options(options)
    return set(options)
  return p

def validate_unambiguous_options(options):
  shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
  longs = [getattr(o.long, 'name') for o in options if o.long is not None]
  dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
  dup_longs = set([n for n in longs if longs.count(n) > 1])
  messages = \
      ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
      ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
  if len(messages):
    from .. import DocoptParseError
    raise DocoptParseError(', '.join(messages))

@generate('short option (-s)')
def option_line_short():
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
def option_line_long():
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
def option_line_opts():
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

def section(strict):
  next_option = nl + optional(indent) + char('-')
  terminator = (nl + nl) ^ (nl + eof()) ^ next_option
  default = (
    regex(r'\[default: ', re.IGNORECASE) >> many(char(illegal='\n]')) << char(']')
  ).desc('[default: ]').parsecmap(join_string)
  doc = many1(char(illegal=default ^ terminator)).desc('option documentation').parsecmap(join_string)

  @generate('options section')
  def p():
    options = []
    yield regex(r'options:', re.I)
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
    return options
  return p
