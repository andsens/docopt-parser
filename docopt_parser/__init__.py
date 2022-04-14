"""
docopt-parser - A parsing library for the docopt helptext
"""
from docopt_parser.doc import parse, DocoptParseError

__all__ = ['parse', 'DocoptParseError']

try:
  # pyright: reportMissingImports=false
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'
