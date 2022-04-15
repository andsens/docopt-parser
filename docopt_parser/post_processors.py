from typing import List, cast
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

  fail_duplicate_documented_options(ast, text)
  match_args_with_options(ast, text)
  # populate_shortcuts(root)
  # mark_multiple(doc)
  warn_unused_documented_options(ast, text)
  return ast

def match_args_with_options(ast: doc.Doc, text: str) -> None:
  def match_opts(node: base.AstLeaf):
    if not isinstance(node, base.AstNode):
      return
    new_items: List[base.AstLeaf] = []
    item_list = iter(node.items)
    # Go through the list pairwise, have each element be "left" once
    left = next(item_list, None)
    while left is not None:
      right = next(item_list, None)
      if isinstance(left, (elements.Short, elements.Long)):
        definition = ast.get_option_definition(left)
        if definition.expects_arg and left.arg is None:
          if isinstance(right, elements.Argument):
            left.arg = right
            # Remove the argument from the list by skipping over it in the next iteration
            right = next(item_list, None)
          else:
            raise doc.DocoptParseError(left.mark.show(
              text,
              f'{left.ident} expects an argument (defined at {definition.mark})')
            )
        elif not definition.expects_arg and left.arg is not None:
          raise doc.DocoptParseError(left.arg.mark.show(
            text,
            f'{left.ident} does not expect an argument (defined at {definition.mark})')
          )
      new_items.append(left)
      left = right
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


# def mark_multiple(node, repeatable=False, siblings=[]):
#   if hasattr(node, 'multiple') and not node.multiple:
#     node.multiple = repeatable or node in siblings
#   elif isinstance(node, groups.Choice):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings)
#   elif isinstance(node, base.AstNode):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
