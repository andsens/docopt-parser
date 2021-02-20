from typing import Union
from docopt_parser.parser_utils import ast_map
from docopt_parser.ast import Choice, DocoptAst, Optional, Sequence

def optimize(ast: DocoptAst):
  ast = remove_single_choice_or_seq(ast)
  ast = remove_nested_choice_or_seq(ast)
  ast = remove_nested_optional(ast)
  return ast

def remove_single_choice_or_seq(ast):
  def mapper(n):
    return n.items[0]

  return ast_map(mapper, ast, lambda n: isinstance(n, (Choice, Sequence)) and len(n.items) == 1)

def remove_nested_choice_or_seq(ast):
  def mapper(n: Union[Choice, Sequence]):
    new_items = []
    for item in n.items:
      if isinstance(item, type(n)):
        new_items += item.items
      else:
        new_items.append(item)
    return type(n)(new_items)

  return ast_map(mapper, ast, lambda n: isinstance(n, (Choice, Sequence)))

def remove_nested_optional(ast):
  def mapper(n: Optional):
    return Optional(n.item.item)
  return ast_map(mapper, ast, lambda n: isinstance(n, Optional) and isinstance(n.item, Optional))
