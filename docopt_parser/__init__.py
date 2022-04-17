"""
docopt-parser - A parsing library for the docopt helptext
"""
from docopt_parser.doc import parse, DocoptError, DocoptParseError
from docopt_parser.base import Group, Leaf, Node, Option
from docopt_parser.groups import Choice, Optional, Repeatable, Sequence
from docopt_parser.leaves import Argument, ArgumentSeparator, Command, DocumentedOption, Long, OptionRef, \
  OptionsShortcut, Short, Text
from docopt_parser.marks import LineNumber, Location, LocInfo, Marked, MarkedTuple, Range, RangeTuple
from docopt_parser.post_processors import merge_identical_leaves

__version__: str
try:
  from .version import __version__  # type: ignore
except ImportError:
  __version__ = '0.0.0-dev'

__all__ = [
  'parse', 'DocoptError', 'DocoptParseError', '__version__', '__doc__',
  'Group', 'Leaf', 'Node', 'Option',
  'Choice', 'Optional', 'Repeatable', 'Sequence',
  'Argument', 'ArgumentSeparator', 'Command', 'DocumentedOption', 'Long', 'OptionRef', 'OptionsShortcut',
  'Short', 'Text',
  'LineNumber', 'Location', 'LocInfo', 'Marked', 'MarkedTuple', 'Range', 'RangeTuple',
  'merge_identical_leaves',
]
