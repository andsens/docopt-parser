from ..astnode import AstNode
from .optionref import OptionRef
from parsec import generate, optional
from .. import char, non_symbol_chars, fail_with, lookahead
from ..short import Short
from ..long import Long
from functools import reduce

class Options(AstNode):
  def __init__(self, options):
    self.options = options

  def __repr__(self):
    return f'''<Options>
{self.indent(self.options)}'''

  def map_references(options, candidates):
    def find(o):
      option = next(filter(lambda opt: o in [opt.short, opt.long], options), None)
      if option is not None:
        return OptionRef(option, o.arg)
      else:
        return o
    return list(map(find, candidates))

  def options(options):
    @generate('Options (-s or --long)')
    def p():
      # Check if we should consume, the lookahead checks if this is unambiguously the
      # beginning of an option. This way we can cause atom() to fail with a useful message
      any_option = char('-') + optional(char('-')) + char(illegal=non_symbol_chars | char('-'))
      yield lookahead(any_option)
      yield char('-')
      known_longs = [o.long.usage_parser for o in options if o.long is not None]
      long_p = reduce(lambda mem, p: mem ^ p, known_longs, fail_with('no --long in Options:'))
      known_shorts = [o.short.usage_parser for o in options if o.short is not None]
      short_p = reduce(lambda mem, p: mem ^ p, known_shorts, fail_with('no -s in Options:'))

      opt = yield long_p | short_p | Long.usage | Short.usage
      opts = [opt]
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(short_p ^ Short.usage)
        if opt is None:
          break
        else:
          opts.append(opt)
      return Options(Options.map_references(options, opts))
    return p
