from typing import Union
from parsec import Parser, Value, one_of, eof, many1, optional, regex, exclude

from docopt_parser import helpers

any_char = regex(r'.|\n').desc('any char')
def char(legal: Union[str, Parser] = any_char, illegal: Union[str, Parser, None] = None) -> Parser:
  if isinstance(legal, str):
    desc = ''
    if len(legal) > 1:
      desc = 'any of '
    desc += ''.join(map(helpers.describe_value, legal))
    a = one_of(legal).desc(desc)
  else:
    a = legal
  if illegal is not None:
    if isinstance(illegal, str):
      desc = ''
      if len(illegal) > 1:
        desc = 'any of '
      desc += ''.join(map(helpers.describe_value, illegal))
      d = one_of(illegal).desc(desc)
    else:
      d = illegal
    d = one_of(illegal) if isinstance(illegal, str) else illegal
    return exclude(a, d)
  else:
    return a

def string(s: str) -> Parser:
    '''Parses a string.'''
    @Parser
    def string_parser(text, index=0):
        slen = len(s)
        if text[index:index + slen] == s:
            return Value.success(index + slen, s)
        else:
            return Value.failure(index, s)
    return string_parser

nl = char('\n')
whitespaces1 = many1(char(' \t', nl)).parsecmap(helpers.join_string).desc('<whitespace>')
whitespaces = optional(whitespaces1)
eol = (whitespaces + (nl | eof())).desc('<end of line>')
indent = (many1(char(' ')) | char('\t')).parsecmap(helpers.join_string).desc('<indent> (spaces or tabs)')
either = char('|').desc('<pipe> (|)')
repeatable = string('...').desc('repeatable (...)')
non_symbol_chars = char('=|()[], \t\n\r\b\f\x1B\x07\0') | eof() | repeatable
