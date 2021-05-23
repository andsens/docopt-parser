from .astnode import AstNode
from .. import DocoptParseError
from . import char, join_string, lookahead, flatten, explain_error
from parsec import regex, many, optional, generate, ParseError
from .option import Option
from .usage.usage import Usage
import re

class DocoptAst(AstNode):
  def __init__(self, usage, options):
    self.usage = usage
    self.options = options

  def __repr__(self):
#     options = '\n'.join([f'''  options:
# {self.indent(section, 2)}''' for section in self.options_sections])
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

  def lang(strict=True):
    @generate('options: sections')
    def options_sections():
      sections = []
      yield DocoptAst.no_options_text
      while (yield lookahead(optional(DocoptAst.re_options_section))) is not None:
        sections.append((yield Option.section(strict) << DocoptAst.no_options_text))
      return sections

    @generate('docopt help text')
    def p():
      # Parse all options sections before parsing the usage section so that we can reference
      # the options while building the usage AST.
      # The lookahead() allows us to parse without consuming the usage section,
      # but any errors will point at the start of the text. So when one occurs we
      # parse again in order to fail properly.
      options = flatten((yield lookahead(options_sections) ^ options_sections))
      DocoptAst.validate_unambiguous_options(options)
      usage = yield (DocoptAst.no_usage_text >> Usage.section(strict, options) << DocoptAst.no_usage_text)
      # DocoptAst.validate_conflicting(options)
      return DocoptAst(usage, options)
    return p

  def parse(txt):
    try:
      return DocoptAst.lang(True).parse_strict(txt)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e

  def parse_partial(txt):
    try:
      return DocoptAst.lang(False).parse_partial(txt)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e
