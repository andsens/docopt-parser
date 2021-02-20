import sys
from typing import Iterable
from docopt_parser.ast import DocoptAst
from parsec import ParseError, Parser, Value

def splat(constr):
  return lambda args: constr(*args)

def unsplat(constr):
  return lambda *args: constr(args)

def flatten_tuples(constr):
  def flatten(arg):
    if isinstance(arg, tuple):
      t = []
      for item in arg:
        t += flatten(item)
      return tuple(t)
    else:
      return [arg]
  return lambda arg: constr(flatten(arg))

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

def ast_tostr(ast: DocoptAst, indent=''):
  tree = ''
  if isinstance(ast, tuple):
    c_indent = indent + '  '
    tree += f'{indent}<{type(ast).__name__}>'
    if 'name' in list(ast._fields):
      tree += f': {ast.name}\n'
    else:
      tree += '\n'
    for key in ast._fields:
      if key == 'name':
        continue
      val = getattr(ast, key)
      if isinstance(val, (tuple, list)):
        tree += f'{c_indent}{key}:\n'
        tree += ast_tostr(val, c_indent)
      else:
        tree += f'{c_indent}{key}: {val}\n'
  elif isinstance(ast, list):
    for item in ast:
      tree += ast_tostr(item, indent)
  else:
    tree += f'{indent}{ast}\n'
  return tree

def ast_map(pred, node, f=lambda n: True):
  outer_pred = pred if f(node) else id
  if isinstance(node, tuple):
    return outer_pred(type(node)(*map(lambda node: ast_map(pred, node, f), node)))
  elif isinstance(node, list):
    return outer_pred(list(map(lambda node: ast_map(pred, node, f), node)))
  else:
    return outer_pred(node)

def ast_collect(pred, ast):
  items = []
  for item in ast:
    if pred(item):
      items.append(item)
    if isinstance(item, (tuple, list)):
      items += ast_collect(pred, item)
  return items

def ast_findall(ast_type, ast):
  return ast_collect(lambda n: isinstance(n, ast_type), ast)

def id(arg):
  return arg
