from parsec import Parser, Value

def splat(constr):
  return lambda args: constr(*args)

def unsplat(constr):
  return lambda *args: constr(args)

def join_string(res):
  flat = ''
  if isinstance(res, list) or isinstance(res, tuple):
    for item in res:
      flat += join_string(item)
    return flat
  else:
    return res

def exclude(p, end):
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

def explain_error(e, text):
  line_no, col = e.loc_info(e.text, e.index)
  line = text.split('\n')[line_no]
  return '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))

def ast_tostr(ast, indent=''):
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
      if isinstance(val, tuple) or isinstance(val, list):
        tree += ast_tostr(val, c_indent)
      else:
        tree += f'{c_indent}{key}: {val}\n'
  elif isinstance(ast, list):
    for item in ast:
      tree += ast_tostr(item, indent)
  else:
    tree += f'{indent}{ast}\n'
  return tree
