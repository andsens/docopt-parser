from typing import Generator, Iterator, Union
from parsec import Parser, generate, optional, regex, eof, many

from docopt_parser.nodes.astleaf import AstLeaf
from .sequence import Sequence
from . import string, whitespaces1, whitespaces, lookahead, nl, non_symbol_chars, indent, eol, char
from .identnode import ident
import re
from .choice import expr, Choice
from .astnode import AstNode
import logging

log = logging.getLogger(__name__)

def section(strict):
  @generate('usage section')
  def p() -> Generator[Parser, Parser, UsageSection]:
    yield regex(r'usage:', re.I)
    yield optional(nl + indent)
    prog = yield lookahead(optional(ident(non_symbol_chars)))
    lines = []
    if prog is not None:
      while True:
        line = yield usage_line(prog)
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
    return UsageSection(root)
  return p

class UsageSection(AstNode):
  root: AstLeaf

  def __init__(self, root: AstLeaf):
    super().__init__([root])
    self.root = root

  def __repr__(self) -> str:
    return f'''<UsageSection>
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[AstLeaf]:
    for item in self.root:
      yield item

def usage_line(prog: str):
  @generate('usage line')
  def p() -> Generator[Parser, Parser, Union[str, AstLeaf]]:
    yield string(prog)
    if (yield optional(lookahead(eol))) is None:
      e = yield whitespaces1 >> expr
    else:
      yield whitespaces
      e = Sequence([])
    return e
  return p
