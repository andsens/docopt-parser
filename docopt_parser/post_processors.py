import warnings
from ordered_set import OrderedSet

from docopt_parser import doc, elements

def post_process_ast(ast: doc.Doc, txt: str) -> doc.Doc:
  # TODO:
  # Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
  # Handle options that are not referenced from usage
  # Find unreachable lines, e.g.:
  #   Usage:
  #     prog ARG
  #     prog cmd <--

  # merge leaves
  # match_options(root)
  warn_unused_options(ast, txt)
  # mark_multiple(doc)
  fail_duplicate_options(ast, txt)
  return ast

def warn_unused_options(ast: doc.Doc, txt: str) -> None:
  if ast.usage_section.reduce(lambda memo, node: memo or isinstance(node, elements.OptionsShortcut), False):
    return
  unused_options = OrderedSet(ast.section_options) - OrderedSet(ast.usage_options)
  for option in unused_options:
    warnings.warn(option.mark.show(txt, message='this option is not referenced from the usage section.'))


def fail_duplicate_options(ast: doc.Doc, txt: str):
  seen_shorts: dict[str, elements.Short] = dict()
  seen_longs: dict[str, elements.Long] = dict()
  messages: list[str] = []
  for option in ast.section_options:
    if option.short is not None:
      previous_short = seen_shorts.get(option.short.name, None)
      if previous_short is not None:
        messages.append(option.short.mark.show(
            txt, message=f'{option.short.ident} has already been specified on line {previous_short.mark.start.line}'
        ))
      else:
        seen_shorts[option.short.name] = option.short
    if option.long is not None:
      previous_long = seen_longs.get(option.long.name, None)
      if previous_long is not None:
        messages.append(option.long.mark.show(
            txt, message=f'{option.long.ident} has already been specified on line {previous_long.mark.start.line}'
        ))
      else:
        seen_longs[option.long.name] = option.long
  if len(messages):
    raise doc.DocoptParseError('\n'.join(messages))

# def match_options(node: base.AstLeaf, known_leaves: OrderedSet[base.AstLeaf] | None = None):
#   if known_leaves is None:
#     known_leaves = OrderedSet[base.AstLeaf]([])
#   if isinstance(node, base.AstNode):
#     for idx, item in enumerate(node.items):
#       if isinstance(item, (elements.Command, elements.Argument, elements.ArgumentSeparator)):
#         if item in known_leaves:
#           node.items[idx] = next(filter(lambda i: i == item, known_leaves))
#         else:
#           known_leaves.add(item)
#       elif isinstance(item, base.AstNode):
#         match_options(item, known_leaves)

# def mark_multiple(node, repeatable=False, siblings=[]):
#   if hasattr(node, 'multiple') and not node.multiple:
#     node.multiple = repeatable or node in siblings
#   elif isinstance(node, groups.Choice):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings)
#   elif isinstance(node, base.AstNode):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
