from docopt_parser.parser_utils import ast_map
from docopt_parser.ast import DocoptAst, Option, OptionRef, Short, Shorts


def resolve_options(ast: DocoptAst):
  ast = merge_option_lines(ast)
  ast = convert_option_lines_to_options(ast)
  ast = resolve_shorts(ast)
  return ast

def resolve_shorts(ast: DocoptAst):
  def mapper(shorts):
    opts = []
    for (i, symbol) in enumerate(shorts.names):
      option = find_option_by_short(symbol, ast.options)
      print(option)
      if option:
        if option.expects_arg:
          arg = shorts[i + 1:] if i + 1 < len(shorts) else None
          opts.append(OptionRef(option, arg))
          break
        else:
          opts.append(OptionRef(option, None))
      # else:
      #   opts.append(Option(Short(symbol)))
      # symbol.arg?
    return opts
  return ast_map(mapper, ast, lambda n: isinstance(n, Shorts))

def find_option_by_short(name, options) -> Option:
  for o in options:
    for opt in o.opts:
      if isinstance(opt, Short) and opt.name == name:
        return o
  return None

def resolve_longs(ast: DocoptAst):
  return ast

def merge_option_lines(ast: DocoptAst):
  option_lines = []
  for options in ast.options:
    option_lines += options
  return DocoptAst(ast.usage, option_lines)

def convert_option_lines_to_options(ast: DocoptAst):
  options = []
  for (opts, doc1, default, doc2) in ast.options:
    doc = ''.join(t for t in [
      '' if doc1 is None else doc1,
      '' if default is None else f'[default: {default}]',
      '' if doc2 is None else doc2,
    ])
    expects_arg = any(i.arg is not None for i in opts)
    options.append(Option(opts, expects_arg, default, doc))
  return DocoptAst(ast.usage, options)
