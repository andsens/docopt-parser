from ..astnode import AstNode
from .optionref import OptionRef
from parsec import generate, optional
from .. import char, join_string, lookahead
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
      known_longs = reduce(lambda mem, p: mem | p, [o.long.usage_parser for o in options if o.long is not None])
      known_shorts = reduce(lambda mem, p: mem | p, [o.short.usage_parser for o in options if o.short is not None])
      opt = yield known_longs | known_shorts | Long.usage | Short.usage
      opts = [opt]
      # multiple short options can be specified like "-abc".
      known_nodash_shorts = reduce(lambda mem, p: mem | p, [
        o.short.nodash_usage_parser for o in options if o.short is not None
      ])
      # Keep parsing if the previously parsed option is a short switch
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(known_nodash_shorts | Short.nodash_usage)
        if opt is None:
          break
        else:
          opts.append(opt)
      return Options(Options.map_references(options, opts))
    return p
