from docopt_parser import DocoptParseError
import re
from .parsec import ParseError, Parser, Value, eof, generate, many, many1, none_of, one_of, optional, regex, sepBy, sepBy1, string
from collections import namedtuple

Multiple = namedtuple('Multiple', ['atom'])
Long = namedtuple('Long', ['name', 'arg'])
Short = namedtuple('Short', ['name', 'arg'])
Shorts = namedtuple('Shorts', ['name', 'arg'])
Command = namedtuple('Command', ['name'])
Expression = namedtuple('Expression', ['select'])
Optional = namedtuple('Optional', ['select'])
Argument = namedtuple('Argument', ['name'])
OptionsShortcut = namedtuple('OptionsShortcut', [])
OptionLine = namedtuple('OptionLine', ['ident', 'default'])
OptionLines = namedtuple('OptionLines', 'lines')
DocoptLang = namedtuple('DocoptLang', ['usage', 'options'])

def splat(constr):
  return lambda args: constr(*args)

def unsplat(constr):
  return lambda *args: constr(args)

def join_string(res):
  flat = ''
  if isinstance(res, list) or isinstance(res, tuple):
    for item in res:
      flat += join_string(item)
    return flat
  else:
    return res

def exclude(p, end):
  '''Fails parser p if parser end matches
  '''
  @Parser
  def exclude_parser(text, index):
    res = end(text, index)
    if res.status:
      return Value.failure(index, 'did not expect {}'.format(res.value))
    else:
      return p(text, index)
  return exclude_parser


def symbol_char(excludes):
  return exclude(any, excludes)

def symbol(excludes):
  return many1(symbol_char(excludes)).desc('symbol').parsecmap(''.join)

multiple = string('...').desc('multiplier (...)')
def multi(of):
  return optional(multiple).parsecmap(lambda m: Multiple(of) if m else of)

def atom(excludes):
  @generate
  def p():
    excl = excludes | multiple
    a = yield (group ^ opt ^ options_shortcut ^ long(excl) ^ shorts(excl) ^ arg ^ command(excl)).bind(multi)
    return a
  return p

def long(excludes):
  return (string('--') >> symbol(excludes | string('=')) + optional(one_of(' =') >> arg)) \
    .desc('long option (--long)').parsecmap(splat(Long))

def short(excludes):
  return (string('-') >> symbol_char(excludes | string('=')) + optional((space | string('=')) >> arg))\
    .desc('short option (-a)').parsecmap(splat(Short))

def shorts(excludes):
  return (string('-') >> many1(symbol_char(excludes | string('='))) + optional((space | string('=')) >> arg))\
    .desc('short options (-abc)').parsecmap(splat(Shorts))

def command(excludes):
  return symbol(excludes).desc('command').parsecmap(Command)

def seq(excludes):
  return sepBy(atom(excludes), exclude(whitespace, nl)).desc('sequence')

def expr(excludes):
  return sepBy(seq(excludes), either).desc('expression').parsecmap(Expression)

any = regex(r'.|\n').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
whitespace = regex(r'\s').desc('<whitespace>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
text = many1(exclude(any, regex(r'options:|usage:', re.I))).desc('Text').parsecmap(join_string)
either = (many(space) >> string('|') << many(space)).desc('<pipe> (|)')
opt = (string('[') >> expr(one_of('| \n]')) << string(']')).desc('[optional]').parsecmap(Optional)
group = (string('(') >> expr(one_of('| \n)')) << string(')')).desc('(group)').parsecmap(Expression)
wrapped_arg = (string('<') + symbol(string('>')) + string('>')).desc('<ARG>').parsecmap(join_string)
uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]+').desc('ARG')
arg = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(Argument)
options_shortcut = string('options').parsecmap(lambda x: OptionsShortcut())

@generate
def usage_lines():
  excludes = one_of('| \n[(')
  prog = yield symbol(excludes)
  yield many(whitespace)
  expressions = [(yield expr(excludes))]
  yield many(whitespace)
  expressions += yield sepBy(string(prog) << many(whitespace) >> expr(excludes), nl + indent)
  return Expression(expressions)

option_default = (
  regex(r'\[default: ', re.IGNORECASE) >> many(none_of('\n]')) << string(']')
).desc('[default: ]').parsecmap(join_string)
option_ident = sepBy1(long(one_of(' \n')) ^ short(one_of(' \n')), one_of(' ,')).desc('option identifier')
option_line_terminator = (nl + nl) ^ (nl + eof()) ^ (nl + indent + string('-'))
option_doc = many1(exclude(any, option_default ^ option_line_terminator)).desc('option documentation')
option_desc = optional(option_doc) >> optional(option_default) << optional(option_doc)

option_line = (
  option_ident + optional(space + many1(space) >> option_desc)
).desc('option line').parsecmap(splat(OptionLine))

option_lines = sepBy(option_line, nl + indent).parsecmap(OptionLines)
usage_section = regex(r'usage:', re.I) >> optional(nl + indent) >> usage_lines << (eof() | nl)
options_section = regex(r'options:', re.I) >> optional(nl + indent) >> option_lines << (eof() | nl)

@generate
def doc():
  options = yield many(text ^ options_section)
  usage = yield usage_section
  options += yield many(text ^ options_section)
  return usage, [o for o in options if isinstance(o, OptionLines)]
docopt_lang = doc.parsecmap(splat(DocoptLang))

def parse(doc):
  try:
    return docopt_lang.parse_strict(doc)
  except ParseError as e:
    raise DocoptParseError(explain_error(e, doc)) from None

def explain_error(e, text):
  line_no, col = e.loc_info(e.text, e.index)
  line = text.split('\n')[line_no]
  return '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))

def ast_tostr(ast, indent=''):
  tree = ''
  if isinstance(ast, tuple):
    c_indent = indent + '  '
    tree += f'{indent}<{type(ast).__name__}>'
    if 'name' in list(ast._fields):
      tree += f': {ast.name}\n'
    else:
      tree += '\n'
    for key in ast._fields:
      if key == 'name':
        continue
      val = getattr(ast, key)
      if isinstance(val, tuple):
        tree += ast_tostr(val, c_indent)
      elif isinstance(val, list):
        for item in val:
          tree += ast_tostr(item, c_indent)
      else:
        tree += f'{c_indent}{key}: {val}\n'
  elif isinstance(ast, list):
    for item in ast:
      tree += ast_tostr(item, indent)
  else:
    tree += f'{indent}{ast}\n'
  return tree
