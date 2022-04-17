import typing as T
import parsec as P
import re

from docopt_parser import base, groups, doc, parsers, helpers, marks

def usage_section(strict: bool):
  @P.generate('usage section')
  def p() -> helpers.GeneratorParser[T.Tuple[str, groups.Choice]]:
    start = yield parsers.location
    yield P.regex(r'usage:', re.I)  # type: ignore
    yield P.optional(parsers.nl + parsers.indent)
    prog = yield parsers.whitespaces >> P.lookahead(base.ident(parsers.non_symbol_chars).desc('a program name'))
    lines: T.List[groups.Choice | groups.Sequence] = []
    if prog is not None:
      while True:
        line = yield usage_line(prog)
        if line is not None:
          lines.append(line)
        if (yield P.optional(parsers.nl + parsers.indent)) is None:
          break
    end = yield parsers.location
    section_ended = yield P.optional(
      ((parsers.nl + parsers.nl) ^ P.many(parsers.char(' \t') | parsers.nl) + P.eof()).result(True)
    )
    if strict and not section_ended:
      err_start, err_char, err_end = yield parsers.char().mark()
      raise doc.DocoptParseError(f'Unexpected {helpers.describe_value(err_char)}', marks.Range((err_start, err_end)))
    return (prog, groups.Choice((start, lines, end)))
  return p


def usage_line(prog: str) -> "P.Parser[groups.Choice | groups.Sequence]":
  # Regarding "type: ignore": Error is
  # Operator ">>" not supported for types "Parser[str]" and "Parser[Choice]" when expected type is "Parser[Sequence]"
  # but parser.__or__(other_parser) works fine, not a clue how to fix this
  return parsers.string(prog) >> (
    (
      P.lookahead(parsers.eol) >> parsers.whitespaces
      .parsecmap(lambda _: []).mark().parsecmap(lambda n: groups.Sequence(n))
    ) | (parsers.whitespaces1 >> groups.expr)  # type: ignore
  )
