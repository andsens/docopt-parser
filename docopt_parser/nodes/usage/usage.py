from parsec import generate, optional, regex, eof
from .sequence import Sequence
from .. import string, whitespaces, lookahead, nl, non_symbol_chars, indent
from ..identnode import ident
import re
from .choice import expr, Choice

class Usage(object):

  def line(prog, options):
    @generate('usage line')
    def p():
      yield string(prog)
      e = yield optional(whitespaces >> expr(options))
      if e is None:
        e = Sequence([])
      return e
    return p

  def section(options):

    @generate('usage section')
    def p():
      yield regex(r'usage:', re.I)
      yield optional(nl + indent)
      prog = yield lookahead(optional(ident(non_symbol_chars)))
      expressions = []
      if prog is not None:
        while True:
          expressions.append((yield Usage.line(prog, options)))
          # consume trailing whitespace
          yield optional(whitespaces)
          if (yield optional(nl + indent)) is None:
            break
      # TODO: must expect two newlines if anything follows
      yield (eof() | nl)
      return Choice(expressions)
    return p
