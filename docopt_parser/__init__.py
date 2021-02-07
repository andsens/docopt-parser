"""
docopt-parser - A parsing library for the docopt helptext
"""

__all__ = ['docopt_parser']
try:
  # pyright: reportMissingImports=false
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'


class DocoptParseError(Exception):
  def __init__(self, message, exit_code=1):
    self.message = message
    self.exit_code = exit_code
