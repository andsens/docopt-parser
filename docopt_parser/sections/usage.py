from typing import Generator, Iterator, Union
from parsec import Parser, generate, optional, regex, eof, many, lookahead
import re

from docopt_parser import base, groups, parsers

def usage_section(strict):
  @generate('usage section')
  def p() -> Generator[Parser, Parser, UsageSection]:
    yield regex(r'usage:', re.I)
    yield optional(parsers.nl + parsers.indent)
    prog = yield lookahead(optional(base.ident(parsers.non_symbol_chars)))
    lines = []
    if prog is not None:
      while True:
        line = yield usage_line(prog)
        if line is not None:
          lines.append(line)
        if (yield optional(parsers.nl + parsers.indent)) is None:
          break
    if strict:
      yield (parsers.nl + parsers.nl) ^ many(parsers.char(' \t') | parsers.nl) + eof()
    else:
      yield optional((parsers.nl + parsers.nl) ^ many(parsers.char(' \t') | parsers.nl) + eof())
    if len(lines) > 1:
      root = groups.Choice(lines)
    elif len(lines) == 1:
      root = lines[0]
    else:
      root = None
    return UsageSection(root)
  return p

class UsageSection(base.AstNode):
  root: base.AstLeaf

  def __init__(self, root: base.AstLeaf):
    super().__init__([root])
    self.root = root

  def __repr__(self) -> str:
    return f'''<UsageSection>
{self.indent(self.items)}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, list[dict]]]]:
    yield 'type', 'usagesection'
    yield 'items', list(map(dict, self.items))

def usage_line(prog: str):
  @generate('usage line')
  def p() -> Generator[Parser, Parser, Union[str, base.AstLeaf]]:
    yield parsers.string(prog)
    if (yield optional(lookahead(parsers.eol))) is None:
      e = yield parsers.whitespaces1 >> groups.choice
    else:
      yield parsers.whitespaces
      e = groups.Sequence([])
    return e
  return p
