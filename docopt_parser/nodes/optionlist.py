from parsec import generate, optional
from .short import Short
from .option import inline_option_spec
from functools import reduce

def option_list(options):
  @generate('Options (-s or --long)')
  def p():
    opt = yield reduce(
      lambda mem, p: p | mem,
      [o.usage_ref for o in options],
      inline_option_spec(options, False)
    )
    opts = [opt]
    # multiple short options can be specified like "-abc".
    shorts = reduce(
      lambda mem, p: p | mem if p is not None else mem,
      [o.shorts_list_usage for o in options],
      inline_option_spec(options, True)
    )
    # Keep parsing if the previously parsed option is a short switch
    while isinstance(opt.ref, Short) and opt.arg is None:
      opt = yield optional(shorts)
      if opt is None:
        break
      else:
        opts.append(opt)
        # Option(short, long, doc1, _default, doc2)
    return opts
  return p
