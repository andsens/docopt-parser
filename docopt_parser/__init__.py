"""
docopt-parser - A parsing library for the docopt helptext
"""
from parsec import ParseError
from .marked import explain_error
from .nodes.doc import Doc, doc as doc_parser
from .nodes.options_shortcut import OptionsShortcut
from .nodes.choice import Choice
from .nodes.command import Command
from .nodes.argument import Argument
from .nodes.argumentseparator import ArgumentSeparator
from .nodes.astnode import AstNode
import warnings
from ordered_set import OrderedSet

__all__ = ['docopt_parser']
try:
  # pyright: reportMissingImports=false
  from .version import __version__
except ImportError:
  __version__ = '0.0.0-dev'

def parse_strict(txt: str) -> Doc:
  try:
    doc = doc_parser(strict=True).parse_strict(txt)
    post_process_ast(doc, txt)
    # TODO: Mark multi elements as such
    return doc
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e

def parse_partial(txt: str) -> Doc:
  try:
    doc, parsed_doc = doc_parser(strict=False).parse_partial(txt)
    post_process_ast(doc, txt)
    return doc, parsed_doc
  except ParseError as e:
    raise DocoptParseError(explain_error(e, txt)) from e


class DocoptParseError(Exception):
  def __init__(self, message: str, exit_code=1):
    self.message = message
    self.exit_code = exit_code


def post_process_ast(doc: Doc, txt: str) -> Doc:
  # merge_identical_leaves(root)
  validate_ununused_options(doc, txt)
  # mark_multiple(doc)
  validate_unambiguous_options(doc, txt)


def validate_unambiguous_options(doc: Doc, txt: str):
  options = doc.section_options
  shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
  longs = [getattr(o.long, 'name') for o in options if o.long is not None]
  dup_shorts = OrderedSet([n for n in shorts if shorts.count(n) > 1])
  dup_longs = OrderedSet([n for n in longs if longs.count(n) > 1])
  messages = \
      ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
      ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
  if len(messages):
    from .. import DocoptParseError
    raise DocoptParseError(', '.join(messages))

def merge_identical_leaves(node, known_leaves=OrderedSet()):
  if isinstance(node, AstNode):
    for idx, item in enumerate(node.items):
      if isinstance(item, (Command, Argument, ArgumentSeparator)):
        if item in known_leaves:
          node.items[idx] = next(filter(lambda i: i == item, known_leaves))
        else:
          known_leaves.add(item)
      elif isinstance(item, AstNode):
        merge_identical_leaves(item, known_leaves)

def validate_ununused_options(doc: Doc, txt: str) -> None:
  if doc.usage.reduce(lambda memo, node: memo or isinstance(node, OptionsShortcut), False):
    return
  unused_options = doc.section_options - doc.usage_options
  for option in unused_options:
    warnings.warn(f'{option.mark.show(txt)} this option is not referenced from the usage section.')

def mark_multiple(node, repeatable=False, siblings=[]):
  if hasattr(node, 'multiple') and not node.multiple:
    node.multiple = repeatable or node in siblings
  elif isinstance(node, Choice):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings)
  elif isinstance(node, AstNode):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
