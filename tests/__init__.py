import typing as T
import hypothesis.strategies as HS
import re

_T = T.TypeVar('_T')

def debug(ret: T.Any, *args: T.Any):
  print(args)
  return ret

def maybe(strategy: HS.SearchStrategy[_T]) -> "HS.SearchStrategy[None | _T]":
  return HS.one_of(HS.none(), strategy)

def chars(legal: "str | None" = None, illegal: "str | None" = None):
  if (legal is None) == (illegal is None):
    raise Exception('char(): legal and illegal parameters are mutually exclusive')
  if legal is not None:
    if len(legal) == 1:
      return HS.just(legal)
    else:
      return HS.sampled_from(legal)
  else:
    return HS.characters(blacklist_characters=illegal)

def idents(illegal: str, starts_with: "HS.SearchStrategy[str] | None" = None):
  if starts_with is not None:
    return HS.tuples(starts_with, HS.text(alphabet=chars(illegal=illegal))).map(lambda t: ''.join(t))
  else:
    return HS.text(alphabet=chars(illegal=illegal), min_size=1)

def not_re(*args: "re.Pattern[str]"):
  def check(s: str):
    return all((r.search(s) is None for r in args))
  return check

nl = chars('\n')
indents = HS.one_of(HS.text(alphabet=chars(' '), min_size=1), chars('\t'))
nl_indent = HS.tuples(chars('\n'), indents).map(''.join)
whitespaces = HS.from_regex(r'\s').filter(lambda s: s != '\n')
