from .usage.optionref import OptionRef
from .astnode import AstNode
from parsec import generate, eof, regex, many1, many
import re
from .long import Long
from .short import Short
from . import optional, string, char, nl, indent, lookahead, whitespaces, eol, fail_with, join_string
from enum import Enum

class SpecSource(Enum):
  USAGE = 'usage'
  OPTIONS = 'options'

class Option(AstNode):

  def __init__(self, short, long, source, doc1, default, doc2):
    super().__init__()
    self.short = short
    self.long = long
    self.source = source
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.default = default
    self.doc = ''.join(t for t in [
      '' if doc1 is None else doc1,
      '' if default is None else f'[default: {default}]',
      '' if doc2 is None else doc2,
    ])

  def __repr__(self):
    return f'''<Option>
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  source:  {self.source.value}
  arg?:    {self.expects_arg}
  default: {self.default}
  doc:     {self.doc}'''

  # usage_ref: Parse references to this option in the usage section
  # shorts_list=True modifies the parser to parse references from the "-abc" short option list syntax
  @property
  def usage_ref(self):
    return self._usage_ref(shorts_list=False)

  @property
  def shorts_list_usage(self):
    return self._usage_ref(shorts_list=True)

  def _usage_ref(self, shorts_list):
    def to_ref(tup):
      ref, arg = tup
      return OptionRef(self, ref, arg)
    if self.short is None:
      if shorts_list:
        return None
      return self.long.usage_ref.parsecmap(to_ref)
    if self.long is None or shorts_list:
      return self.short._usage_ref(shorts_list).parsecmap(to_ref)
    return (
      self.short._usage_ref(shorts_list)
      | self.long.usage_ref
    ).parsecmap(to_ref)

  # inline_spec_usage: Parses an option that is specified inline in the usage section and adds it to the options list
  def inline_spec_usage(options, shorts_list):

    @generate('inline option spec')
    def p():
      if shorts_list:
        opt = yield Short.shorts_list_inline_spec_usage
      else:
        opt = yield (Short.inline_spec_usage | Long.inline_spec_usage)
      if isinstance(opt, Short):
        option = Option(opt, None, SpecSource.USAGE, None, None, None)
      else:
        option = Option(None, opt, SpecSource.USAGE, None, None, None)
      ref = OptionRef(option, opt, opt.arg)
      options.append(option)
      return ref
    return p

  @generate('options')
  def opts():
    first = yield Long.options | Short.options
    if isinstance(first, Long):
      opt_short = yield optional((string(', ') | char(' ')) >> Short.options)
      opt_long = first
    else:
      opt_short = first
      opt_long = yield optional((string(', ') | char(' ')) >> Long.options)
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
        (short, long) = yield Option.opts
        if (yield optional(lookahead(eol))) is not None:
          # Consume trailing whitespaces
          yield whitespaces
        elif (yield optional(lookahead(char(illegal='\n')))) is not None:
          yield (char(' ') + many1(char(' '))) ^ fail_with('at least 2 spaces')
          doc1 = yield optional(doc)
          _default = yield optional(default)
          doc2 = yield optional(doc)
        options.append(Option(short, long, SpecSource.OPTIONS, doc1, _default, doc2))
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
