"""
docopt-parser - A parsing library for the docopt helptext
"""

__all__ = ['docopt_parser']
try:
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'
