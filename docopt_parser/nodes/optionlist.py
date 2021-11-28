from parsec import generate, optional
from .short import Short, inline_short_option_spec, inline_shortlist_short_option_spec
from .long import inline_long_option_spec

@generate('Options (-s or --long)')
def option_list():
  opt = yield inline_short_option_spec | inline_long_option_spec
  opts = [opt]
  # multiple short options can be specified like "-abc".
  # Keep parsing if the previously parsed option is a short switch
  while isinstance(opt, Short) and opt.arg is None:
    opt = yield optional(inline_shortlist_short_option_spec)
    if opt is None:
      break
    else:
      opts.append(opt)
  return opts
