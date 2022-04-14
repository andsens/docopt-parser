from typing import List
from parsec import generate, optional, regex, eof, many, lookahead  # type: ignore
import re

from docopt_parser import base, groups, parsers
from docopt_parser.helpers import GeneratorParser

def usage_section(strict: bool):
  @generate('usage section')
  def p() -> GeneratorParser[UsageSection]:
    yield regex(r'usage:', re.I)
    yield optional(parsers.nl + parsers.indent)
    prog = yield lookahead(optional(base.ident(parsers.non_symbol_chars)))
    lines: List[groups.Choice | groups.Sequence] = []
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
  root: groups.Choice | groups.Sequence | None

  def __init__(self, root: groups.Choice | groups.Sequence | None):
    if root is None:
      super().__init__([])
    else:
      super().__init__([root])
    self.root = root

  def __repr__(self) -> str:
    return f'''<UsageSection>
{self.indent(self.items)}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'type', 'usagesection'
    yield 'items', [dict(item) for item in self.items]

def usage_line(prog: str):
  @generate('usage line')
  def p() -> GeneratorParser[groups.Choice | groups.Sequence]:
    yield parsers.string(prog)
    if (yield optional(lookahead(parsers.eol))) is None:
      return (yield parsers.whitespaces1 >> groups.choice)
    else:
      yield parsers.whitespaces
      return groups.Sequence([])
  return p
