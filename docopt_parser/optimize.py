from docopt_parser.ast import Choice, DocoptAst, Optional, Options, Sequence

def optimize(ast: DocoptAst):
  ast = ast_map(remove_single_choice_or_seq, ast)
  ast = ast_map(remove_nested_choice_or_seq, ast)
  ast = ast_map(remove_nested_optional, ast)
  ast = merge_options(ast)
  return ast

def ast_map(pred, ast):
  if isinstance(ast, tuple):
    return pred(type(ast)(*map(lambda node: ast_map(pred, node), ast)))
  elif isinstance(ast, list):
    return pred(list(map(lambda node: ast_map(pred, node), ast)))
  else:
    return pred(ast)

def remove_single_choice_or_seq(ast):
  if isinstance(ast, (Choice, Sequence)) and len(ast.items) == 1:
    return ast.items[0]
  else:
    return ast

def remove_nested_choice_or_seq(ast):
  if isinstance(ast, (Choice, Sequence)):
    new_items = []
    for item in ast.items:
      if isinstance(item, type(ast)):
        new_items += item.items
      else:
        new_items.append(item)
    return type(ast)(new_items)
  else:
    return ast

def remove_nested_optional(ast):
  if isinstance(ast, Optional) and isinstance(ast.item, Optional):
    return Optional(ast.item.item)
  else:
    return ast

def merge_options(ast: DocoptAst):
  option_lines = []
  for options in ast.options:
    option_lines += options.lines
  return DocoptAst(ast.usage, [Options(option_lines)])
