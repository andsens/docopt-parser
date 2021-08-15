from parsec import generate, optional, regex, eof, many
from .sequence import Sequence
from . import string, whitespaces1, whitespaces, lookahead, nl, non_symbol_chars, indent, eol, char, join_string
from .identnode import ident
import re
from .choice import expr, Choice
from .option import Option
from .optionref import OptionRef
import logging

log = logging.getLogger(__name__)

no_usage_text = many(char(illegal=regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)
def usage_section(options, strict=True):
  return no_usage_text >> section(strict, options) << no_usage_text

def section(strict, options):
  @generate('usage section')
  def p():
    yield regex(r'usage:', re.I)
    yield optional(nl + indent)
    prog = yield lookahead(optional(ident(non_symbol_chars)))
    lines = []
    if prog is not None:
      while True:
        line = yield usage_line(prog, options)
        if line is not None:
          lines.append(line)
        if (yield optional(nl + indent)) is None:
          break
    if strict:
      yield (nl + nl) ^ many(char(' \t') | nl) + eof()
    else:
      yield optional((nl + nl) ^ many(char(' \t') | nl) + eof())
    if len(lines) > 1:
      root = Choice(lines)
    elif len(lines) == 1:
      root = lines[0]
    else:
      root = None
    validate_ununused_options(root, options)
    return root
  return p

def usage_line(prog, options):
  @generate('usage line')
  def p():
    yield string(prog)
    if (yield optional(lookahead(eol))) is None:
      e = yield whitespaces1 >> expr(options)
    else:
      yield whitespaces
      e = Sequence([])
    return e
  return p

def validate_ununused_options(node, all_options):
  if node is None:
    return

  def get_opts(options, node):
    if isinstance(node, Option):
      options.add(node)
    if isinstance(node, OptionRef):
      options.add(node.ref)
    return options
  used_options = node.reduce(get_opts, set())
  unused_options = all_options - used_options
  if len(unused_options) > 0:
    unused_list = '\n'.join(map(lambda o: f'* {o.ident}', unused_options))
    log.warn(f'''{len(unused_options)} options are not referenced from the usage section:
{unused_list}''')
