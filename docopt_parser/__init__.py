"""
docopt-parser - A parsing library for the docopt helptext
"""
from docopt_parser.errors import DocoptError, DocoptParseError
from docopt_parser.base import Group, Leaf, Node
from docopt_parser.groups import Choice, Optional, Repeatable, Sequence
from docopt_parser.leaves import Argument, ArgumentSeparator, Command, OptionsShortcut, Option
from docopt_parser.marks import LineNumber, Location, LocInfo, Marked, MarkedTuple, Range, RangeTuple
from docopt_parser.post_processors import merge_identical_leaves

__version__: str
try:
  from .version import __version__  # type: ignore
except ImportError:
  __version__ = '0.0.0-dev'

__all__ = [
  'parse', 'DocoptError', 'DocoptParseError', '__version__', '__doc__',
  'Group', 'Leaf', 'Node',
  'Choice', 'Optional', 'Repeatable', 'Sequence',
  'Argument', 'ArgumentSeparator', 'Command', 'OptionsShortcut', 'Option',
  'LineNumber', 'Location', 'LocInfo', 'Marked', 'MarkedTuple', 'Range', 'RangeTuple',
  'merge_identical_leaves',
]


def parse(text: str) -> Group:
  import parsec as P
  from docopt_parser import usage, leaves, errors, marks, post_processors
  try:
    options = leaves.documented_options.parse_strict(text)
    documented_options = options.copy()
    root = usage.usage(options).parse_strict(text)
    root = post_processors.post_process_ast(root, documented_options, text)
    return root
  except errors.DocoptParseError as e:
    if e.mark is not None:
      raise errors.DocoptError(e.mark.show(text, e.message), e.exit_code) from e
    else:
      raise errors.DocoptError(e.message, e.exit_code) from e
  except P.ParseError as e:
    loc = marks.Location(e.loc_info(e.text, e.index))
    raise errors.DocoptError(loc.show(text, str(e))) from e
