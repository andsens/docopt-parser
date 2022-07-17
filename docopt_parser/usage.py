import typing as T
import parsec as P
import re

from docopt_parser import base, groups, leaves
from docopt_parser.util import helpers, parsers, marks

section_title = P.regex(r'[^\n]*usage:', re.I)  # type: ignore
non_usage_section_text = P.optional(parsers.text(section_title))
prog = (
  base.ident(illegal=(parsers.whitespaces1 | parsers.eol))
  .desc('a program name').parsecmap(helpers.join_string).mark()
  .parsecmap(lambda n: marks.Marked(n))
)
prog_in_usage = (
  non_usage_section_text >> section_title
  >> P.optional(parsers.nl + parsers.indent) >> parsers.whitespaces
  >> prog << parsers.text(None)
)


def usage(options: T.List[leaves.Option]):
  @P.generate('usage section')
  def p() -> helpers.GeneratorParser[groups.Choice]:

    yield non_usage_section_text
    start = yield parsers.location
    yield section_title
    yield P.optional(parsers.nl + parsers.indent)
    prog_name = yield parsers.whitespaces >> P.lookahead(prog)

    next_line = parsers.eol + parsers.indent
    lines: T.List[groups.Choice] = []
    while True:
      lines.append((yield usage_line(prog_name.elm, options)))
      if (yield P.lookahead(P.optional(next_line))) is None:
        break
      yield next_line
    end = yield parsers.location
    yield parsers.eol
    yield non_usage_section_text
    return groups.Choice((start, lines, end))
  return p


def usage_line(prog: str, options: T.List[leaves.Option]):
  return parsers.string(prog) >> (
    (
      P.lookahead(parsers.eol) >> parsers.whitespaces
      .parsecmap(lambda _: []).mark().parsecmap(lambda n: groups.Choice(n))
    ) | (
      parsers.whitespaces1 >> groups.expr(options)
    )
  ) << P.lookahead(parsers.eol)
