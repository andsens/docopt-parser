from docopt_parser.parser_utils import ast_findall
from tests.docopt import DocoptLanguageError
from docopt_parser.ast import DocoptAst, Long, Short

def validate(ast: DocoptAst):
  validate_unambiguous_options(ast)
  # validate_options_have_arguments(ast)

def validate_unambiguous_options(ast):
  shorts = [getattr(o, 'name') for o in ast_findall(Short, ast.options)]
  longs = [getattr(o, 'name') for o in ast_findall(Long, ast.options)]
  dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
  dup_longs = set([n for n in longs if longs.count(n) > 1])
  messages = \
      ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
      ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
  if len(messages):
    raise DocoptLanguageError(', '.join(messages))
