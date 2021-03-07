from hypothesis.strategies import one_of, characters, just, text, from_regex, \
  sets, tuples, none, composite, lists, sampled_from, integers, shared, booleans, \
  fixed_dictionaries, deferred, recursive, permutations
from collections import namedtuple
import re

def maybe(gen):
  return one_of(none(), gen)

def chars(legal=None, illegal=None):
  if (legal is None) == (illegal is None):
    raise Exception('char(): legal and illegal parameters are mutually exclusive')
  if legal is not None:
    if len(legal) == 1:
      return just(legal)
    else:
      return sampled_from(legal)
  else:
    return characters(blacklist_characters=illegal)

def idents(illegal, starts_with=None):
  if starts_with is not None:
    return tuples(starts_with, text(alphabet=chars(illegal=illegal))).map(lambda t: ''.join(t))
  else:
    return text(alphabet=chars(illegal=illegal), min_size=1)

def not_re(*args):
  def check(s):
    return all((r.search(s) is None for r in args))
  return check

nl = chars('\n')
indents = one_of(text(alphabet=chars(' '), min_size=1), chars('\t'))
