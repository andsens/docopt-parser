import typing as T
from ordered_set import OrderedSet
import logging

from docopt_parser import base, leaves, groups

log = logging.getLogger(__name__)
TNode = T.TypeVar('TNode', bound=base.Node)


def post_process_ast(root: base.Group, documented_options: T.List[leaves.Option], text: str):
  # TODO:
  # Find unreachable lines, e.g.:
  #   Usage:
  #     prog ARG
  #     prog cmd <--
  # TODO: Merge nested Repeatables with only one child

  populate_shortcuts(root, documented_options, text)
  root = convert_root_to_optional_on_empty_lines(root)
  root = collapse_groups(root)
  mark_multiple(root)
  merge_identical_leaves(root)
  return root


def populate_shortcuts(root: base.Group, documented_options: T.List[leaves.Option], text: str) -> None:
  # Option shortcuts contain to all documented options except the ones
  # that are explicitly mentioned in the usage section

  def get_opts(memo: T.List[leaves.Option], node: base.Node):
    if isinstance(node, leaves.Option):
      memo.append(node.definition)
    return memo

  shortcut_options = OrderedSet((o.definition for o in documented_options)) - OrderedSet(root.reduce(get_opts, []))

  def populate(node: base.Node):
    if isinstance(node, leaves.OptionsShortcut):
      return groups.Optional(node.mark.wrap_element([
        leaves.Option(node.mark.wrap_element(o.ident).to_marked_tuple(), None, definition=o)
        for o in shortcut_options
      ]).to_marked_tuple())
    return node
  root.replace(populate)

  unused_options = OrderedSet((o.definition for o in documented_options)) - OrderedSet(root.reduce(get_opts, []))
  for option in unused_options:
    log.warning(option.mark.show(text, f'{option.ident} is not referenced from the usage section'))


def convert_root_to_optional_on_empty_lines(root: base.Group) -> base.Group:
  # Ensure the root is optional when giving no parameters is valid.
  # e.g.
  #   Usage:
  #     prog
  #     prog a
  #
  # A less obvious example (options will end up as an empty optional, because -f is used in the next line):
  #   Usage:
  #     prog options
  #     prog -f
  #   Options:
  #     -f

  def get_leaves(memo: T.List[base.Leaf], node: base.Node):
    if isinstance(node, base.Leaf):
      memo.append(node)
    return memo

  for item in root.items:
    if isinstance(item, base.Group) and len(item.reduce(get_leaves, [])) == 0:
      return groups.Optional(root.mark.wrap_element([root]).to_marked_tuple())
  return root


def collapse_groups(root: base.Group) -> base.Group:
  root_mark = root.mark

  def coerce_to_sequence(node: "base.Node | None") -> base.Group:
    if node is None:
      items: T.List[base.Node] = []
      return groups.Sequence(root_mark.wrap_element(items).to_marked_tuple())
    elif not isinstance(node, base.Group):
      return groups.Sequence(root_mark.wrap_element([node]).to_marked_tuple())
    return node

  def remove_empty_groups(node: TNode) -> "TNode | None":
    if isinstance(node, (base.Group)) and len(node.items) == 0:
      return None
    return node
  root = coerce_to_sequence(root.replace(remove_empty_groups))

  def remove_intermediate_groups_with_one_item(node: base.Node) -> base.Node:
    if isinstance(node, (groups.Choice, groups.Sequence)) and len(node.items) == 1:
      return node.items[0]
    return node
  root = coerce_to_sequence(root.replace(remove_intermediate_groups_with_one_item))

  def merge_nested_sequences(node: base.Node) -> base.Node:
    if isinstance(node, groups.Sequence):
      new_items: T.List[base.Node] = []
      for item in node.items:
        if isinstance(item, groups.Sequence):
          new_items += item.items
        else:
          new_items.append(item)
      node.items = new_items
    return node
  root = coerce_to_sequence(root.replace(merge_nested_sequences))

  def dissolve_groups(node: base.Node) -> base.Node:
    # Must run after merge_nested_sequences so that [(a b c)] does not become [a b c]
    if isinstance(node, groups.Group):
      assert len(node.items) == 1
      return node.items[0]
    return node
  root = coerce_to_sequence(root.replace(dissolve_groups))

  def merge_neighboring_sequences(node: base.Node) -> base.Node:
    new_items: T.List[base.Node] = []
    if isinstance(node, groups.Sequence):
      new_items: T.List[base.Node] = []
      # Go through the list pairwise, have each element be "left" once
      item_list = iter(node.items)
      left = next(item_list, None)
      while left is not None:
        right = next(item_list, None)
        if isinstance(left, groups.Sequence) and isinstance(right, groups.Sequence):
          left.items = list(left.items) + list(right.items)
          # Skip the right Sequence in the next iteration, but repeat for the left Sequence
          # so we can merge with another potential Sequence
          right = left
        new_items.append(left)
        left = right
      node.items = new_items
    return node
  root = coerce_to_sequence(root.replace(merge_neighboring_sequences))

  def remove_intermediate_groups_in_optionals(node: base.Node) -> base.Node:
    if isinstance(node, groups.Optional):
      if isinstance(node.items[0], (groups.Sequence, groups.Optional)) and len(node.items) == 1:
        node.items = node.items[0].items
    return node
  root = coerce_to_sequence(root.replace(remove_intermediate_groups_in_optionals))

  def remove_nested_repeatables(node: base.Node) -> base.Node:
    if isinstance(node, (groups.Repeatable)):
      assert len(node.items) == 1
      if isinstance(node.items[0], (groups.Repeatable)):
        return node.items[0]
    return node
  root = coerce_to_sequence(root.replace(remove_nested_repeatables))

  return root


def mark_multiple(root: base.Group) -> None:
  # Mark leaves that can be specified multiple times
  marked_leaves: T.Set[base.Leaf] = set()

  def mark_from_repeatable(node: base.Node, multiple: bool = False):
    if isinstance(node, (base.Group)):
      for item in node.items:
        mark_from_repeatable(item, multiple or isinstance(node, groups.Repeatable))
    else:
      assert isinstance(node, (base.Leaf))
      if multiple:
        node.multiple = multiple
        marked_leaves.add(node)
  mark_from_repeatable(root)

  def mark_repeated(node: base.Node, possible_siblings: T.Set[base.Leaf]) -> T.Set[base.Leaf]:
    # Mark nodes that are mentioned more than once on a path through the tree
    if isinstance(node, (groups.Choice)):
      # Siblings between choice do not affect each other. e.g. (a | a) does not mean a can be specified multiple times
      new_siblings: T.Set[base.Leaf] = set()
      for item in node.items:
        new_siblings |= mark_repeated(item, possible_siblings)
      possible_siblings = possible_siblings.union(new_siblings)
    elif isinstance(node, (base.Group)):
      for item in node.items:
        possible_siblings = possible_siblings.union(mark_repeated(item, possible_siblings))
    else:
      assert isinstance(node, (base.Leaf))
      if any([node == leaf for leaf in possible_siblings]):
        node.multiple = True
        marked_leaves.add(node)
      # set.add(node) would mutate the set from parent calls
      possible_siblings = possible_siblings.union(set([node]))
    return possible_siblings
  mark_repeated(root, set())

  def mark_identical_nodes(node: base.Node):
    # For some reason we can't use "node in set()"
    # Also the reason for the type ignore
    if any([node == leaf for leaf in marked_leaves]):
      node.multiple = True  # type: ignore
    return node
  root.replace(mark_identical_nodes)


def merge_identical_leaves(root: base.Group, ignore_option_args: bool = False) -> base.Group:
  known_leaves: T.Set[base.Leaf] = set()

  def merge(node: base.Node):
    if isinstance(node, base.Leaf):
      for leaf in known_leaves:
        if node == leaf:
          if not ignore_option_args \
            and isinstance(node, leaves.Option) and node.arg != leaf.arg:  # type: ignore
            # Preserve argument names of options
            return node
          return leaf
      known_leaves.add(node)
    return node
  return T.cast(base.Group, root.replace(merge))
