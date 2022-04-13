from typing import Generator
from parsec import Parser, generate, optional

from docopt_parser import elements

@generate('Options (-s or --long)')
def option_list() -> Generator[Parser, Parser, list[elements.Short, elements.Long]]:
  opt = yield elements.inline_short_option_spec | elements.inline_long_option_spec
  opts = [opt]
  # multiple short options can be specified like "-abc".
  # Keep parsing if the previously parsed option is a short switch
  while isinstance(opt, elements.Short) and opt.arg is None:
    opt = yield optional(elements.inline_shortlist_short_option_spec)
    if opt is None:
      break
    else:
      opts.append(opt)
  return opts
