from typing import TypeVar, Union
from parsec import Parser, Value, one_of, eof, many1, optional, regex

# TODO:
# Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
# Handle options that are not referenced from usage

def splat(constr):
  return lambda args: constr(*args)

def unsplat(constr):
  return lambda *args: constr(args)

def flatten(arg: Union[tuple, list]) -> Union[tuple, list]:
  if not isinstance(arg, (tuple, list)):
    from .. import DocoptParseError
    raise DocoptParseError('flatten(arg): argument not a tuple or list')
  t = []
  for item in arg:
    if isinstance(item, (tuple, list)):
      t += [elm for elm in item]
    else:
      t.append(item)
  return type(arg)(t)

T = TypeVar('T')
def debug(arg: T) -> T:
  import sys
  sys.stderr.write('{}\n'.format(arg))
  return arg

def join_string(res: Union[list, tuple, str]) -> str:
  flat = ''
  if isinstance(res, list) or isinstance(res, tuple):
    for item in res:
      flat += join_string(item)
    return flat
  else:
    return res

char_descriptions = {
  ' ': '<space>',
  '\n': '<newline>',
  '\t': '<tab>',
  '|': '<pipe> (|)'
}

def describe_value(val: str) -> str:
  if len(val) > 1:
    return val
  return char_descriptions.get(val, f'"{val}" ({hex(ord(val))})')

any_char = regex(r'.|\n').desc('any char')
def char(legal: Union[str, Parser] = any_char, illegal: Union[str, Parser, None] = None) -> Parser:
  if isinstance(legal, str):
    desc = ''
    if len(legal) > 1:
      desc = 'any of '
    desc += ''.join(map(describe_value, legal))
    a = one_of(legal).desc(desc)
  else:
    a = legal
  if illegal is not None:
    if isinstance(illegal, str):
      desc = ''
      if len(illegal) > 1:
        desc = 'any of '
      desc += ''.join(map(describe_value, illegal))
      d = one_of(illegal).desc(desc)
    else:
      d = illegal
    d = one_of(illegal) if isinstance(illegal, str) else illegal
    return exclude(a, d)
  else:
    return a

def fail_with(message: str) -> Parser:
  return Parser(lambda _, index: Value.failure(index, message))

def exclude(p: Parser, excl: Parser) -> Parser:
  '''Fails parser p if parser excl matches'''
  @Parser
  def exclude_parser(text, index):
    res = excl(text, index)
    if res.status:
      return Value.failure(index, f'something other than {describe_value(res.value)}')
    else:
      return p(text, index)
  return exclude_parser

def lookahead(p: Parser) -> Parser:
  '''Parses without consuming'''
  @Parser
  def lookahead_parser(text, index):
    res = p(text, index)
    if res.status:
      return Value.success(index, res.value)
    else:
      return Value.failure(index, res.expected)
  return lookahead_parser

def unit(p: Parser) -> Parser:
  '''Converts a parser into a single unit
  Only consumes input if the parser succeeds'''
  @Parser
  def unit_parser(text, index):
    res = p(text, index)
    if res.status:
      return Value.success(res.index, res.value)
    else:
      return Value.failure(index, res.expected)
  return unit_parser

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
whitespaces1 = many1(char(' \t', nl)).parsecmap(join_string).desc('<whitespace>')
whitespaces = optional(whitespaces1)
eol = (whitespaces + (nl | eof())).desc('<end of line>')
indent = (many1(char(' ')) | char('\t')).parsecmap(join_string).desc('<indent> (spaces or tabs)')
either = char('|').desc('<pipe> (|)')
repeatable = string('...').desc('repeatable (...)')
non_symbol_chars = char('=|()[], \t\n\r\b\f\x1B\x07\0') | eof() | repeatable
