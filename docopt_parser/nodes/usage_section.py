from parsec import generate, optional, regex, eof, many
from .sequence import Sequence
from . import string, whitespaces1, whitespaces, lookahead, nl, non_symbol_chars, indent, eol, char, join_string
from .identnode import ident
import re
from .choice import expr, Choice

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
      return Choice(lines)
    else:
      return lines[0] if len(lines) else Choice([])
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
