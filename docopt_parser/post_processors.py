from typing import List
import warnings
from ordered_set import OrderedSet

from docopt_parser import doc, base, elements

def post_process_ast(ast: doc.Doc, text: str) -> doc.Doc:
  # TODO:
  # Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
  # Handle options that are not referenced from usage
  # Find unreachable lines, e.g.:
  #   Usage:
  #     prog ARG
  #     prog cmd <--

  match_args_with_options(ast, text)
  # match_options(root)
  # merge leaves
  # populate_shortcuts(root)
  warn_unused_documented_options(ast, text)
  # mark_multiple(doc)
  fail_duplicate_documented_options(ast, text)
  return ast

def match_args_with_options(ast: doc.Doc, text: str) -> None:
  def match_opts(node: base.AstLeaf):
    if not isinstance(node, base.AstNode):
      return
    prev = None
    new_items: List[base.AstLeaf] = []
    for item in node.items:
      if isinstance(prev, (elements.Short, elements.Long)):
        definition = ast.get_option_definition(prev)
        if definition.expects_arg:
          if prev.arg is None:
            if isinstance(item, elements.Argument):
              prev.arg = item
            else:
              raise doc.DocoptParseError(prev.mark.show(
                text,
                f'{prev.ident} expects an argument (defined at {definition.mark})')
              )
          else:
            new_items.append(item)
        elif prev.arg is not None:
          raise doc.DocoptParseError(prev.mark.show(
            text,
            f'{prev.ident} does not expect an argument (defined at {definition.mark})')
          )
        else:
          new_items.append(item)
      else:
        new_items.append(item)
      prev = item
    node.items = new_items
  ast.walk(match_opts)

def warn_unused_documented_options(ast: doc.Doc, text: str) -> None:
  if ast.usage_section.reduce(lambda memo, node: memo or isinstance(node, elements.OptionsShortcut), False):
    return
  unused_options = OrderedSet(ast.section_options) - OrderedSet(ast.usage_options)
  for option in unused_options:
    warnings.warn(option.mark.show(text, message='this option is not referenced from the usage section.'))


def fail_duplicate_documented_options(ast: doc.Doc, text: str):
  seen_shorts: dict[str, elements.Short] = dict()
  seen_longs: dict[str, elements.Long] = dict()
  messages: list[str] = []
  for option in ast.section_options:
    if option.short is not None:
      previous_short = seen_shorts.get(option.short.name, None)
      if previous_short is not None:
        messages.append(option.short.mark.show(
            text, message=f'{option.short.ident} has already been specified on line {previous_short.mark.start.line}'
        ))
      else:
        seen_shorts[option.short.name] = option.short
    if option.long is not None:
      previous_long = seen_longs.get(option.long.name, None)
      if previous_long is not None:
        messages.append(option.long.mark.show(
            text, message=f'{option.long.ident} has already been specified on line {previous_long.mark.start.line}'
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
