from typing import TypeVar, Union

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
