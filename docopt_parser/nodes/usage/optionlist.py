from ..astnode import AstNode
from .optionref import OptionRef
from parsec import generate, optional
from ..short import Short
from ..long import Long
from functools import reduce

class OptionList(AstNode):
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
      opt = yield reduce(
        lambda mem, p: p | mem,
        [o.long.usage_parser for o in options if o.long is not None]
        + [o.short.usage_parser for o in options if o.short is not None],
        Long.usage | Short.usage
      )
      opts = [opt]
      # multiple short options can be specified like "-abc".
      shorts = reduce(
        lambda mem, p: p | mem,
        [o.short.nodash_usage_parser for o in options if o.short is not None],
        Short.nodash_usage
      )
      # Keep parsing if the previously parsed option is a short switch
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(shorts)
        if opt is None:
          break
        else:
          opts.append(opt)
      return OptionList(OptionList.map_references(options, opts))
    return p
