import sys
from tests.docopt import DocoptLanguageError
from parsec import ParseError, Parser, Value

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

def exclude(p: Parser, end: Parser):
  '''Fails parser p if parser end matches
  '''
  @Parser
  def exclude_parser(text, index):
    res = end(text, index)
    if res.status:
      return Value.failure(index, 'did not expect {}'.format(res.value))
    else:
      return p(text, index)
  return exclude_parser

def explain_error(e: ParseError, text: str):
  line_no, col = e.loc_info(e.text, e.index)
  line = text.split('\n')[line_no]
  return '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))
