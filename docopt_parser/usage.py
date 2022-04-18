import typing as T
import parsec as P
import re

from docopt_parser import base, groups, leaves, parsers, helpers

def usage(options: T.List[leaves.Option]):
  @P.generate('usage section')
  def p() -> helpers.GeneratorParser[groups.Choice]:
    section_title = P.regex(r'[^\n]*usage:', re.I)  # type: ignore
    non_usage_section_text = P.optional(parsers.text(section_title))

    yield non_usage_section_text
    start = yield parsers.location
    yield section_title
    yield P.optional(parsers.nl + parsers.indent)
    prog = yield parsers.whitespaces >> P.lookahead(base.ident(parsers.non_symbol_chars).desc('a program name'))

    lines: T.List[groups.Choice] = []
    while True:
      line = yield usage_line(prog, options)
      if line is not None:
        lines.append(line)
      if (yield P.optional(parsers.indent)) is None:
        break
    end = yield parsers.location
    yield non_usage_section_text
    return groups.Choice((start, lines, end))
  return p


def usage_line(prog: str, options: T.List[leaves.Option]) -> "P.Parser[groups.Choice]":
  return parsers.string(prog) >> (
    (
      P.lookahead(parsers.eol) >> parsers.whitespaces
      .parsecmap(lambda _: []).mark().parsecmap(lambda n: groups.Choice(n))
    ) | (
      parsers.whitespaces1 >> groups.expr(options)
    )
  ) << parsers.eol
