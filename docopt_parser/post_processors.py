import warnings
from ordered_set import OrderedSet

from docopt_parser import base, elements, groups, doc

def post_process_ast(ast: doc.Doc, txt: str) -> doc.Doc:
  # TODO:
  # Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
  # Handle options that are not referenced from usage

  # match_options(root)
  validate_ununused_options(ast, txt)
  # mark_multiple(doc)
  validate_unambiguous_options(ast, txt)

def match_options(node, known_leaves=OrderedSet()):
  if isinstance(node, base.AstNode):
    for idx, item in enumerate(node.items):
      if isinstance(item, (elements.Command, elements.Argument, elements.ArgumentSeparator)):
        if item in known_leaves:
          node.items[idx] = next(filter(lambda i: i == item, known_leaves))
        else:
          known_leaves.add(item)
      elif isinstance(item, base.AstNode):
        match_options(item, known_leaves)


def validate_unambiguous_options(ast: doc.Doc, txt: str):
  options = ast.section_options
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

def validate_ununused_options(ast: doc.Doc, txt: str) -> None:
  if ast.usage.reduce(lambda memo, node: memo or isinstance(node, elements.OptionsShortcut), False):
    return
  unused_options = ast.section_options - ast.usage_options
  for option in unused_options:
    warnings.warn(f'{option.mark.show(txt)} this option is not referenced from the usage section.')

def mark_multiple(node, repeatable=False, siblings=[]):
  if hasattr(node, 'multiple') and not node.multiple:
    node.multiple = repeatable or node in siblings
  elif isinstance(node, groups.Choice):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings)
  elif isinstance(node, base.AstNode):
    for item in node.items:
      mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
