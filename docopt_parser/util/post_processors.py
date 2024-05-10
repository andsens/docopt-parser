import typing as T
from ordered_set import OrderedSet
import logging

from docopt_parser import base, leaves, groups
from docopt_parser.util.marks import Range

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
  # print(new_root)
  new_root = convert_root_to_optional_on_empty_lines(root)
  new_root = collapse_groups(new_root)
  mark_multiple(new_root)
  merge_identical_leaves(new_root)
  return new_root


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
      return groups.Optional(node.mark << [
        leaves.Option(node.mark << o.ident, None, definition=o)
        for o in shortcut_options
      ])
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
      return groups.Optional(root.mark << [root])
  return root


def collapse_groups(root: base.Node) -> base.Node:
  changed = True
  root_mark = root.mark

  # A [] B () -> A B
  def remove_empty_groups(node: TNode) -> "TNode | None":
    nonlocal changed
    if isinstance(node, base.Group) and len(node.items) == 0:
      changed = True
      # print(inspect.stack()[0].function)
      return None
    return node

  # A (B) C -> A B C
  def remove_intermediate_groups_with_one_item(node: base.Node) -> base.Node:
    nonlocal changed
    if isinstance(node, (groups.Choice, groups.Sequence)) and len(node.items) == 1:
      changed = True
      # print(inspect.stack()[0].function)
      node.items[0].mark = node.mark
      return node.items[0]
    return node

  # A (B C) -> A B C
  def merge_nested_sequences(node: base.Node):
    nonlocal changed
    if isinstance(node, groups.Sequence):
      new_items: T.List[base.Node] = []
      for item in node.items:
        if isinstance(item, groups.Sequence):
          changed = True
          new_items += item.items
        else:
          new_items.append(item)
      node.items = new_items

  # [A [B [C]]] -> [A B C]
  def merge_nested_optionals(node: base.Node):
    nonlocal changed
    if isinstance(node, groups.Optional):
      new_items: T.List[base.Node] = []
      for item in node.items:
        if isinstance(item, groups.Optional):
          changed = True
          new_items += item.items
        else:
          new_items.append(item)
      node.items = new_items

  # (A) -> A
  # Must run after remove_root_sequence_in_optionals so that [(a b c)] does not become [a b c]
  def dissolve_groups(node: base.Node) -> base.Node:
    nonlocal changed
    if isinstance(node, groups.Group):
      changed = True
      # print(inspect.stack()[0].function)
      assert len(node.items) == 1
      node.items[0].mark = node.mark
      return node.items[0]
    return node

  # (A B C) (D E F) -> A B C D E F
  def merge_neighboring_sequences(node: base.Node):
    nonlocal changed
    new_items: T.List[base.Node] = []
    if isinstance(node, groups.Sequence):
      new_items: T.List[base.Node] = []
      # Go through the list pairwise, have each element be "left" once
      item_list = iter(node.items)
      left = next(item_list, None)
      while left is not None:
        right = next(item_list, None)
        if isinstance(left, groups.Sequence) and isinstance(right, groups.Sequence):
          changed = True
          left.items = list(left.items) + list(right.items)
          left.mark = Range(((left.mark.start.line, left.mark.start.col), (right.mark.end.line, right.mark.end.col)))
          # Skip the right Sequence in the next iteration, but repeat for the left Sequence
          # so we can merge with another potential Sequence
          right = left
        new_items.append(left)
        left = right
      node.items = new_items

  # A|(B|C) -> A|B|C
  def merge_nested_choices(node: base.Node):
    nonlocal changed
    if isinstance(node, groups.Choice):
      new_items: T.List[base.Node] = []
      for item in node.items:
        if isinstance(item, groups.Choice):
          changed = True
          new_items += item.items
        else:
          new_items.append(item)
      node.items = new_items

  # (A...)... -> A...
  def remove_nested_repeatables(node: base.Node) -> base.Node:
    nonlocal changed
    if isinstance(node, (groups.Repeatable)):
      if isinstance(node.items[0], (groups.Repeatable)):
        changed = True
        # print(inspect.stack()[0].function)
        return node.items[0]
    return node

  # A|A -> A
  def remove_same_choice(node: base.Node):
    nonlocal changed
    if isinstance(node, (groups.Choice)):
      new_items: T.List[base.Node] = []
      for item in node.items:
        if not any([item == new_item for new_item in new_items]):
          new_items.append(item)
        else:
          changed = True
      node.items = new_items

  new_root = root.replace(dissolve_groups)
  if new_root is None:  # type: ignore
    return groups.Sequence(root_mark << [])  # type: ignore
  i = 0
  # Run until nothing can be remove any longer
  while changed:
    changed = False
    new_root = new_root.replace(remove_empty_groups)
    if new_root is None:
      return groups.Sequence(root_mark << [])  # type: ignore
    new_root = new_root.replace(remove_intermediate_groups_with_one_item)
    if new_root is None:  # type: ignore
      return groups.Sequence(root_mark << [])  # type: ignore
    new_root.walk(merge_nested_sequences)
    new_root.walk(merge_nested_optionals)
    new_root.walk(merge_neighboring_sequences)
    new_root.walk(merge_nested_choices)
    new_root = new_root.replace(remove_nested_repeatables)
    if new_root is None:  # type: ignore
      return groups.Sequence(root_mark << [])  # type: ignore
    new_root.walk(remove_same_choice)
    i += 1
    if i > 100:
      raise Exception(new_root)

  return new_root


def mark_multiple(root: base.Node) -> None:
  # Mark leaves that can be specified multiple times
  marked_leaves: T.Set[base.Leaf] = set()

  def mark_from_repeatable(node: base.Node, multiple: bool = False):
    if isinstance(node, (base.Group)):
      for item in node.items:
        mark_from_repeatable(item, multiple or isinstance(node, groups.Repeatable))
    else:
      assert isinstance(node, (base.Leaf))
      if multiple:
        node.set_multiple(True)
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
        node.set_multiple(True)
        marked_leaves.add(node)
      # set.add(node) would mutate the set from parent calls
      possible_siblings = possible_siblings.union(set([node]))
    return possible_siblings
  mark_repeated(root, set())

  def mark_identical_nodes(node: base.Node):
    # For some reason we can't use "node in set()"
    # Also the reason for the type ignore
    if any([node == leaf for leaf in marked_leaves]):
      node.set_multiple(True)  # type: ignore
    return node
  root.replace(mark_identical_nodes)


def merge_identical_leaves(root: base.Node, ignore_option_args: bool = False) -> base.Node:
  known_leaves: T.Set[base.Leaf] = set()

  def merge(node: base.Node):
    if isinstance(node, base.Leaf):
      for leaf in known_leaves:
        if node == leaf:
          if not ignore_option_args \
            and isinstance(node, leaves.Option) and node.argname != leaf.argname:  # type: ignore
            # Preserve argument names of options
            return node
          return leaf
      known_leaves.add(node)
    return node
  new_root = root.replace(merge)
  if new_root is None:  # type: ignore
    return groups.Sequence(root.mark << [])  # type: ignore
  else:
    return new_root


def merge_identical_groups(root: base.Node) -> base.Node:
  known_groups: T.Set[base.Group] = set()

  def merge(node: base.Node) -> base.Node:
    if isinstance(node, base.Group):
      for group in known_groups:
        if type(node) == type(group) and node.items == group.items:
          return group
      known_groups.add(node)
    return node
  new_root = root.replace(merge)
  if new_root is None:  # type: ignore
    return groups.Sequence(root.mark << [])  # type: ignore
  else:
    return new_root
