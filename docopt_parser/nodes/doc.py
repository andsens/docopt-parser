from .command import Command
from .argument import Argument
from .argumentseparator import ArgumentSeparator
from parsec import regex, many, many1, generate
from . import char, join_string, flatten
import re
from .astnode import AstNode
from .options_section import OptionsSection, section as options_section
from .usage_section import UsageSection, section as usage_section
from .option import Option
from .optionref import OptionRef
import logging

log = logging.getLogger(__name__)

other_documentation = many1(char(illegal=regex(r'[^\n]*(options:|usage:)', re.I))).desc('Text').parsecmap(join_string)

def doc(strict):
  @generate('docopt')
  def p():
    items = list(filter(lambda part: part != [], (yield (
      many(options_section(strict) | other_documentation)
      + usage_section(strict)
      + many(options_section(strict) | other_documentation)
    ).parsecmap(flatten))))
    # if isinstance(section, UsageSection):
    #   if usage is not None:
    #     raise section.error('')
    #   else:
    #     usage = section
    # merge_identical_leaves(root)
    # validate_ununused_options(root)
    # mark_multiple(root)
    # validate_unambiguous_options(options)
    return Doc(items)
  return p

class Doc(AstNode):
  def __init__(self, items):
    super().__init__(items)
    self.doc = next(filter(lambda n: isinstance(n, UsageSection), self.items), None)
    self.options = list(filter(lambda n: isinstance(n, OptionsSection), self.items))

  def __repr__(self):
    return f'''{self.indent(self.items, lvl=0)}'''

  def __iter__(self):
    yield 'usage', dict(self.doc)
    yield 'options', list(map(dict, self.options))


def validate_unambiguous_options(options):
  shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
  longs = [getattr(o.long, 'name') for o in options if o.long is not None]
  dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
  dup_longs = set([n for n in longs if longs.count(n) > 1])
  messages = \
      ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
      ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
  if len(messages):
    from .. import DocoptParseError
    raise DocoptParseError(', '.join(messages))

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
