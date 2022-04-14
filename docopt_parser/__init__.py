"""
docopt-parser - A parsing library for the docopt helptext
"""
from docopt_parser.doc import parse, DocoptParseError

try:
  from .version import __version__  # type: ignore
except ImportError:
  __version__ = '0.0.0-dev'

__all__ = ['parse', 'DocoptParseError', '__version__', '__doc__']
