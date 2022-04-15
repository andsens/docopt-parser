from typing import Generator, List, TypeVar, Iterable, Any, overload
from parsec import Parser

T = TypeVar('T')
GeneratorParser = Generator["Parser[Any]", Any, T]

def debug(arg: T) -> T:
  import sys
  sys.stderr.write('{}\n'.format(arg))
  return arg

Nested = T | Iterable["Nested[T]"]
@overload
def join_string(elm: Nested[str]) -> str:
  pass
@overload
def join_string(elm: Nested[None]) -> None:
  pass
@overload
def join_string(elm: Nested[str | None]) -> str | None:
  pass

def join_string(elm: Nested[str | None]) -> str | None:
  if elm is None or isinstance(elm, (str)):
    return elm
  else:
    flat: List[str | None] = []
    for item in elm:
      flat.append(join_string(item))
    filtered = list(e for e in flat if e is not None)
    if len(filtered) > 0:
      return ''.join(filtered)
    else:
      return None

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
