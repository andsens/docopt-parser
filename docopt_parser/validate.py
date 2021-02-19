from tests.docopt import DocoptLanguageError
from docopt_parser.ast import DocoptAst, Short

def validate(ast: DocoptAst):
  validate_unambiguous_short(ast)

def find(pred, ast: DocoptAst):
  items = []
  for item in ast:
    if pred(item):
      items.append(item)
    if isinstance(item, (tuple, list)):
      items += find(pred, item)
  return items

def validate_unambiguous_short(ast):
  seen_shorts = ''
  for short in find(lambda n: isinstance(n, Short), ast):
    if short.name in seen_shorts:
      raise DocoptLanguageError('-%s is specified more than once' % short.name)
    seen_shorts += short.name
