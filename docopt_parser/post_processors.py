import typing as T
import warnings
from ordered_set import OrderedSet

from docopt_parser import doc, base, leaves, groups

def post_process_ast(ast: doc.Doc, text: str) -> doc.Doc:
  # TODO:
  # Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
  # Handle options that are not referenced from usage
  # Find unreachable lines, e.g.:
  #   Usage:
  #     prog ARG
  #     prog cmd <--

  collapse_groups(ast, text)
  fail_duplicate_documented_options(ast, text)
  update_short_option_idents(ast, text)
  match_args_with_options(ast, text)
  populate_shortcuts(ast, text)
  # mark_multiple(doc)
  warn_unused_documented_options(ast, text)
  return ast


def collapse_groups(ast: doc.Doc, text: str):
  pass

def fail_duplicate_documented_options(ast: doc.Doc, text: str):
  # Fail when an option section defines an option twice, e.g.:
  # Options:
  #   -f, --long
  #   -a, --long
  seen_shorts: dict[str, leaves.Short] = dict()
  seen_longs: dict[str, leaves.Long] = dict()
  messages: T.List[str] = []
  for option in ast.section_options:
    if option.short is not None:
      previous_short = seen_shorts.get(option.short.ident, None)
      if previous_short is not None:
        messages.append(option.short.mark.show(
            text, message=f'{option.short.ident} has already been specified on line {previous_short.mark.start.line}'
        ))
      else:
        seen_shorts[option.short.ident] = option.short
    if option.long is not None:
      previous_long = seen_longs.get(option.long.ident, None)
      if previous_long is not None:
        messages.append(option.long.mark.show(
            text, message=f'{option.long.ident} has already been specified on line {previous_long.mark.start.line}'
        ))
      else:
        seen_longs[option.long.ident] = option.long
  if len(messages):
    raise doc.DocoptParseError('\n'.join(messages))


def update_short_option_idents(ast: doc.Doc, text: str) -> None:
  # Change the identifiers of short option to their long counterpart (if any)
  # in order to ease comparisons for processing further down the line

  def update(node: base.AstNode):
      if isinstance(node, (leaves.Short)):
        node.ident = ast.get_option_definition(node).ident
  ast.usage.walk(update)

def match_args_with_options(ast: doc.Doc, text: str) -> None:
  # When parsing initially "-a ARG" is parsed as two unrelated nodes
  # This method moves that "ARG" into the option, when e.g. the doc looks like this:
  # Usage: prog -a ARG
  # Options:
  #   -a ARG
  def match_opts(node: base.AstNode):
    if not isinstance(node, base.AstGroup):
      return
    new_items: T.List[base.AstNode] = []
    item_list = iter(node.items)
    # Go through the list pairwise, have each element be "left" once
    left = next(item_list, None)
    while left is not None:
      right = next(item_list, None)
      if isinstance(left, (leaves.Short, leaves.Long)):
        definition = ast.get_option_definition(left)
        if definition.expects_arg and left.arg is None:
          if isinstance(right, leaves.Argument):
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
  ast.usage.walk(match_opts)

def populate_shortcuts(ast: doc.Doc, text: str) -> None:
  # Option shortcuts contain to all documented options except the ones
  # that are explicitly mentioned in the usage section
  shortcut_options = OrderedSet(ast.section_options) - OrderedSet(ast.usage_options)

  def populate(node: base.AstNode):
    if isinstance(node, (base.AstGroup)):
      new_items: T.List[base.AstNode] = []
      for item in node.items:
        if isinstance(item, leaves.OptionsShortcut):
          start = (item.mark.start.line, item.mark.start.col)
          end = (item.mark.end.line, item.mark.end.col)
          item = groups.Optional((start, list(shortcut_options), end))
        new_items.append(item)
      node.items = new_items
  ast.usage.walk(populate)


def warn_unused_documented_options(ast: doc.Doc, text: str) -> None:
  if ast.usage.reduce(lambda memo, node: memo or isinstance(node, leaves.OptionsShortcut), False):
    return
  unused_options = OrderedSet(ast.section_options) - OrderedSet(ast.usage_options)
  for option in unused_options:
    warnings.warn(option.mark.show(text, message='this option is not referenced from the usage section.'))

# def mark_multiple(node, repeatable=False, siblings=[]):
#   if hasattr(node, 'multiple') and not node.multiple:
#     node.multiple = repeatable or node in siblings
#   elif isinstance(node, groups.Choice):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings)
#   elif isinstance(node, base.AstNode):
#     for item in node.items:
#       mark_multiple(item, repeatable or node.repeatable, siblings + [i for i in node.items if i != item])
