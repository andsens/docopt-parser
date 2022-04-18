import typing as T
import parsec as P

_T = T.TypeVar('_T')
GeneratorParser = T.Generator["P.Parser[T.Any]", T.Any, _T]

def debug(arg: _T) -> _T:
  import sys
  sys.stderr.write('{}\n'.format(arg))
  return arg

Nested = T.Union[_T, T.Sequence["Nested[_T]"]]

@T.overload
def join_string(elm: Nested[str]) -> str:
  pass
@T.overload
def join_string(elm: Nested[None]) -> None:
  pass
@T.overload
def join_string(elm: Nested["str | None"]) -> "str | None":
  pass

def join_string(elm: Nested["str | None"]) -> "str | None":
  if elm is None or isinstance(elm, (str)):
    return elm
  else:
    flat: T.List["str | None"] = []
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
