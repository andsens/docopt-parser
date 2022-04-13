"""
docopt-parser - A parsing library for the docopt helptext
"""
# from . import base, groups, sections, doc, helpers, parsers, marked, post_processors

# __all__ = ['base', 'groups', 'sections', 'doc', 'helpers', 'parsers', 'marked', 'post_processors', 'doc']

from docopt_parser.doc import parse, DocoptParseError

__all__ = ['parse', 'DocoptParseError']

try:
  # pyright: reportMissingImports=false
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'
