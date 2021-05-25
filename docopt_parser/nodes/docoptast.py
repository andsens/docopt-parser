from .astnode import AstNode
from .. import DocoptParseError
from . import char, join_string, lookahead, explain_error
from parsec import regex, many, optional, generate, ParseError
from .option import Option
from .usage.usage import Usage
import re

class DocoptAst(AstNode):
  def __init__(self, usage, options):
    self.usage = usage
    self.options = options

  def __repr__(self):
    return f'''<Docopt>
  usage:
{self.indent([self.usage], 2)}
  options:
{self.indent(self.options, 2)}'''

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

  def options(strict=True):
    @generate('options: sections')
    def p():
      opts = []
      yield DocoptAst.no_options_text
      while (yield lookahead(optional(DocoptAst.re_options_section))) is not None:
        opts.extend((yield Option.section(strict) << DocoptAst.no_options_text))
      DocoptAst.validate_unambiguous_options(opts)
      return opts
    return p

  def usage(options, strict=True):
    return DocoptAst.no_usage_text >> Usage.section(strict, options) << DocoptAst.no_usage_text

  def parse(txt):
    try:
      options = DocoptAst.options(strict=True).parse_strict(txt)
      usage = DocoptAst.usage(options, strict=True).parse_strict(txt)
      return DocoptAst(usage, options)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e

  def parse_partial(txt):
    try:
      options, _ = DocoptAst.options(strict=False).parse_partial(txt)
      usage, parsed_doc = DocoptAst.usage(options, strict=False).parse_partial(txt)
      return DocoptAst(usage, options), parsed_doc
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e
