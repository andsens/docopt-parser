"""
docopt-parser - A parsing library for the docopt helptext
"""
from parsec import ParseError
from .nodes.doc import doc

__all__ = ['docopt_parser']
try:
  # pyright: reportMissingImports=false
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'

def explain_error(e: ParseError, text: str):
  line_no, col = e.loc_info(e.text, e.index)
  lines = text.split('\n')
  prev_line = ''
  if line_no > 0:
    prev_line = lines[line_no - 1] + '\n'
  line = lines[line_no]
  col = ' ' * col
  msg = str(e)
  return f'\n{prev_line}{line}\n{col}^\n{msg}'

def parse_strict(txt):
  try:
    usage = doc(strict=True).parse_strict(txt)
    # TODO: Mark multi elements as such
    return usage
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e

def parse_partial(txt):
  try:
    usage, parsed_doc = doc(strict=False).parse_partial(txt)
    return usage, parsed_doc
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e


class DocoptParseError(Exception):
  def __init__(self, message, exit_code=1):
    self.message = message
    self.exit_code = exit_code
