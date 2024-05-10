"""
docopt-parser - A parsing library for the docopt helptext
"""
import re

from docopt_parser.base import Group, Leaf, Node
from docopt_parser.groups import Choice, Optional, Repeatable, Sequence
from docopt_parser.leaves import Argument, ArgumentSeparator, Command, OptionsShortcut, Option
from docopt_parser.util import DocoptError, DocoptParseError, \
  LineNumber, Location, LocInfo, Marked, MarkedTuple, Range, RangeTuple
from docopt_parser.util.post_processors import merge_identical_leaves, merge_identical_groups, collapse_groups

__all__ = [
  'parse', 'get_prog', 'DocoptError', 'DocoptParseError',
  'Group', 'Leaf', 'Node',
  'Choice', 'Optional', 'Repeatable', 'Sequence',
  'Argument', 'ArgumentSeparator', 'Command', 'OptionsShortcut', 'Option',
  'LineNumber', 'Location', 'LocInfo', 'Marked', 'MarkedTuple', 'Range', 'RangeTuple',
  'merge_identical_leaves', 'merge_identical_groups', 'collapse_groups'
]


def parse(text: str) -> Node:
  import parsec as P
  from docopt_parser import usage, leaves
  from docopt_parser.util import post_processors, errors, marks
  try:
    options = leaves.documented_options.parse_strict(text)  # type: ignore
    documented_options = options.copy()
    root = usage.usage(options).parse_strict(text)  # type: ignore
    root = post_processors.post_process_ast(root, documented_options, text)
    return root
  except errors.DocoptParseError as e:
    if e.mark is not None:
      raise errors.DocoptError(e.mark.show(text, e.message), e.exit_code) from e
    else:
      raise errors.DocoptError(e.message, e.exit_code) from e
  except P.ParseError as e:
    (line, col) = e.loc_info(e.text, e.index)  # type: ignore
    loc = marks.Location((line, col))
    err = re.sub(f'{line}:{col}$', str(loc), str(e))
    raise errors.DocoptError(loc.show(text, err)) from e


def get_prog(text: str) -> Marked[str]:
  import parsec as P
  from docopt_parser import usage
  from docopt_parser.util import errors, marks
  try:
    return usage.prog_in_usage.parse_strict(text)  # type: ignore
  except errors.DocoptParseError as e:
    if e.mark is not None:
      raise errors.DocoptError(e.mark.show(text, e.message), e.exit_code) from e
    else:
      raise errors.DocoptError(e.message, e.exit_code) from e
  except P.ParseError as e:
    (line, col) = e.loc_info(e.text, e.index)  # type: ignore
    loc = marks.Location((line, col))
    err = re.sub(f'{line}:{col}$', str(loc), str(e))
    raise errors.DocoptError(loc.show(text, err)) from e
