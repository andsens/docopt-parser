from parsec import generate, optional, regex, eof
from .sequence import Sequence
from .. import string, whitespaces, lookahead, nl, non_symbol_chars, indent, eol
from ..identnode import ident
import re
from .choice import expr, Choice

class Usage(object):
  def line(prog, options):
    @generate('usage line')
    def p():
      yield string(prog)
      if (yield optional(lookahead(eol))) is None:
        e = yield whitespaces >> expr(options)
      else:
        yield optional(whitespaces)
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
        yield (nl + nl) | whitespaces + eof()
      else:
        yield optional((nl + nl) | whitespaces + eof())
      return Choice(expressions)
    return p
