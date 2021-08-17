from .command import Command
from .argument import Argument
from .argumentseparator import ArgumentSeparator
from parsec import generate, optional, regex, eof, many
from .sequence import Sequence
from . import string, whitespaces1, whitespaces, lookahead, nl, non_symbol_chars, indent, eol, char, join_string
from .identnode import ident
import re
from .choice import expr, Choice
from .option import Option
from .optionref import OptionRef
from .astnode import AstNode
import logging

log = logging.getLogger(__name__)

no_usage_text = many(char(illegal=regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)
def usage_section(options, strict=True):
  return no_usage_text >> section(strict, options) << no_usage_text

def section(strict, options):
  @generate('usage section')
  def p():
    yield regex(r'usage:', re.I)
    yield optional(nl + indent)
    prog = yield lookahead(optional(ident(non_symbol_chars)))
    lines = []
    if prog is not None:
      while True:
        line = yield usage_line(prog, options)
        if line is not None:
          lines.append(line)
        if (yield optional(nl + indent)) is None:
          break
    if strict:
      yield (nl + nl) ^ many(char(' \t') | nl) + eof()
    else:
      yield optional((nl + nl) ^ many(char(' \t') | nl) + eof())
    if len(lines) > 1:
      root = Choice(lines)
    elif len(lines) == 1:
      root = lines[0]
    else:
      root = None
    merge_identical_leaves(root)
    validate_ununused_options(root, options)
    mark_multiple(root)
    return root
  return p

def usage_line(prog, options):
  @generate('usage line')
  def p():
    yield string(prog)
    if (yield optional(lookahead(eol))) is None:
      e = yield whitespaces1 >> expr(options)
    else:
      yield whitespaces
      e = Sequence([])
    return e
  return p

def merge_identical_leaves(node, known_leaves=set()):
  if isinstance(node, AstNode):
    for idx, item in enumerate(node.items):
      if isinstance(item, (Command, Argument, ArgumentSeparator)):
        if item in known_leaves:
          node.items[idx] = next(filter(lambda i: i == item, known_leaves))
        else:
          known_leaves.add(item)
      elif isinstance(item, AstNode):
        merge_identical_leaves(item, known_leaves)

def validate_ununused_options(node, all_options):
  def get_opts(options, node):
    if isinstance(node, Option):
      options.add(node)
    if isinstance(node, OptionRef):
      options.add(node.ref)
    return options
  used_options = node.reduce(get_opts, set()) if node else set()
  unused_options = all_options - used_options
  if len(unused_options) > 0:
    unused_list = '\n'.join(map(lambda o: f'* {o.ident}', unused_options))
    log.warn(f'''{len(unused_options)} options are not referenced from the usage section:
{unused_list}''')

def mark_multiple(node, repeatable=False, siblings=[]):
  if hasattr(node, 'multiple') and not node.multiple:
    node.multiple = repeatable or node in siblings
  elif isinstance(node, Choice):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings)
  elif isinstance(node, AstNode):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
