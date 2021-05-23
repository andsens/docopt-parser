from parsec import generate, optional, regex, eof, many
from .sequence import Sequence
from .. import string, whitespaces1, whitespaces, lookahead, nl, non_symbol_chars, indent, eol, char
from ..identnode import ident
import re
from .choice import expr, Choice

class Usage(object):
  def line(prog, options):
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

  def section(strict, options):
    @generate('usage section')
    def p():
      yield regex(r'usage:', re.I)
      yield optional(nl + indent)
      prog = yield lookahead(optional(ident(non_symbol_chars)))
      expressions = []
      if prog is not None:
        while True:
          expressions.append((yield Usage.line(prog, options)))
          if (yield optional(nl + indent)) is None:
            break
      if strict:
        yield (nl + nl) ^ many(char(' \t') | nl) + eof()
      else:
        yield optional((nl + nl) ^ many(char(' \t') | nl) + eof())
      return Choice(expressions)
    return p
