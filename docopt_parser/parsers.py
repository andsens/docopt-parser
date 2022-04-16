import typing as T
import parsec as P

from docopt_parser import helpers, marks

any_char = P.regex(r'.|\n').desc('any char')  # type: ignore
def char(legal: "str | P.Parser[str]" = any_char, illegal: "P.Parser[T.Any] | str | None" = None) -> "P.Parser[str]":
  if isinstance(legal, str):
    desc = ''
    if len(legal) > 1:
      desc = 'any of '
    desc += ''.join(map(helpers.describe_value, legal))
    a = P.one_of(legal).desc(desc)
  else:
    a = legal
  if illegal is not None:
    if isinstance(illegal, str):
      desc = ''
      if len(illegal) > 1:
        desc = 'any of '
      desc += ''.join(map(helpers.describe_value, illegal))
      d = P.one_of(illegal).desc(desc)
    else:
      d = illegal
    d = P.one_of(illegal) if isinstance(illegal, str) else illegal
    return P.exclude(a, d)  # type: ignore
  else:
    return a

def string(s: str) -> "P.Parser[str]":
  '''Parses a string.'''
  @P.Parser
  def string_parser(text: str, index: int = 0) -> P.Value[str]:
    slen = len(s)
    if text[index:index + slen] == s:
      return P.Value.success(index + slen, s)
    else:
      return T.cast(P.Value[str], P.Value.failure(index, s))
  return string_parser

@P.Parser
def location(text: str, index: int = 0) -> P.Value[marks.LocInfo]:
  '''Returns the current location of the parser'''
  return P.Value.success(index, P.ParseError.loc_info(text, index))

nl = char('\n')
whitespaces1 = P.many1(char(' \t', nl)).parsecmap(helpers.join_string).desc('<whitespace>')
whitespaces = P.optional(whitespaces1)
eol = (whitespaces + (nl | P.eof())).desc('<end of line>')
indent = (P.many1(char(' ')) | char('\t')).parsecmap(helpers.join_string).desc('<indent> (spaces or tabs)')
either = char('|').desc('<pipe> (|)')
ellipsis = string('...').desc('ellipsis (...)')
non_symbol_chars = char('=|()[], \t\n\r\b\f\x1B\x07\0') | P.eof() | ellipsis
