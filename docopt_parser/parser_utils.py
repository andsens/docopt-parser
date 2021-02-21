import sys
from tests.docopt import DocoptLanguageError
from parsec import ParseError, Parser, Value, one_of, regex

def splat(constr):
  return lambda args: constr(*args)

def unsplat(constr):
  return lambda *args: constr(args)

def flatten(arg):
  if not isinstance(arg, (tuple, list)):
    raise DocoptLanguageError('flatten(arg): argument not a tuple or list')
  t = []
  for item in arg:
    if isinstance(item, (tuple, list)):
      t += [elm for elm in item]
    else:
      t.append(item)
  return type(arg)(t)

def debug(arg):
  sys.stderr.write('{}\n'.format(arg))
  return arg

def join_string(res):
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

def describe_value(val):
  if len(val) > 1:
    return val
  return char_descriptions.get(val, val)

def exclude(p: Parser, end: Parser):
  '''Fails parser p if parser end matches
  '''
  @Parser
  def exclude_parser(text, index):
    res = end(text, index)
    if res.status:
      return Value.failure(index, f'something other than {describe_value(res.value)}')
    else:
      return p(text, index)
  return exclude_parser

any_char = regex(r'.|\n').desc('any char')
def char(legal=any_char, illegal=None):
  if isinstance(legal, str):
    desc = ' or '.join(map(describe_value, legal))
    a = one_of(legal).desc(desc)
  else:
    a = legal
  if illegal is not None:
    if isinstance(illegal, str):
      desc = ' or '.join(map(describe_value, illegal))
      d = one_of(illegal).desc(desc)
    else:
      d = illegal
    d = one_of(illegal) if isinstance(illegal, str) else illegal
    return exclude(a, d)
  else:
    return a

def lookahead(p: Parser):
  '''Parses without consuming
  '''
  @Parser
  def lookahead_parser(text, index):
    res = p(text, index)
    if res.status:
      return Value.success(index, res.value)
    else:
      return Value.failure(index, res.value)
  return lookahead_parser

def explain_error(e: ParseError, text: str):
  line_no, col = e.loc_info(e.text, e.index)
  lines = text.split('\n')
  prev_line = ''
  if line_no > 0:
    prev_line = lines[line_no - 1] + '\n'
  line = lines[line_no]
  col = ' ' * col
  msg = str(e)
  return f'{prev_line}{line}\n{col}^\n{msg}'
