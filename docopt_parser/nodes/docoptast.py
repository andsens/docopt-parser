from .. import DocoptParseError
from . import char, join_string, lookahead, explain_error
from parsec import regex, many, optional, generate, ParseError
from .option import Option
from .usage.usage import Usage
import re

def validate_unambiguous_options(options):
  shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
  longs = [getattr(o.long, 'name') for o in options if o.long is not None]
  dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
  dup_longs = set([n for n in longs if longs.count(n) > 1])
  messages = \
      ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
      ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
  if len(messages):
    raise DocoptParseError(', '.join(messages))

re_options_section = regex(r'options:', re.I)
no_options_text = many(char(illegal=re_options_section)).desc('Text').parsecmap(join_string)
no_usage_text = many(char(illegal=regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)

def option_sections(strict=True):
  @generate('options: sections')
  def p():
    opts = []
    yield no_options_text
    while (yield lookahead(optional(re_options_section))) is not None:
      opts.extend((yield Option.section(strict) << no_options_text))
    validate_unambiguous_options(opts)
    return opts
  return p

def usage_section(options, strict=True):
  return no_usage_text >> Usage.section(strict, options) << no_usage_text

def parse_strict(txt):
  try:
    options = option_sections(strict=True).parse_strict(txt)
    usage = usage_section(options, strict=True).parse_strict(txt)
    # TODO: Warn about unreferenced options
    # TODO: Mark multi elements as such
    return usage
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e

def parse_partial(txt):
  try:
    options, _ = option_sections(strict=False).parse_partial(txt)
    usage, parsed_doc = usage_section(options, strict=False).parse_partial(txt)
    return usage, parsed_doc
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e
