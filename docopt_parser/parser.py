from docopt_parser.ast import Argument, Command, DocoptAst, Choice, Long, \
  Multiple, OptionLine, Optional, Options, OptionsShortcut, Sequence, Short, Shorts
from docopt_parser.parser_utils import exclude, join_string, splat
import re
from parsec import eof, generate, many, many1, none_of, one_of, optional, regex, sepBy, sepBy1, string

any = regex(r'.|\n').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
whitespace = regex(r'\s').desc('<whitespace>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')

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
  return sepBy(atom(excludes), exclude(whitespace, nl)).desc('sequence').parsecmap(Sequence)

def expr(excludes):
  return sepBy(seq(excludes), either).desc('expression').parsecmap(Choice)

text = many1(exclude(any, regex(r'options:|usage:', re.I))).desc('Text').parsecmap(join_string)
either = (many(space) >> string('|') << many(space)).desc('<pipe> (|)')
opt = (string('[') >> expr(one_of('| \n][(')) << string(']')).desc('[optional]').parsecmap(Optional)
group = (string('(') >> expr(one_of('| \n)([')) << string(')')).desc('(group)')
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
  return Choice(expressions)

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

option_lines = sepBy(option_line, nl + indent).parsecmap(Options)
usage_section = regex(r'usage:', re.I) >> optional(nl + indent) >> usage_lines << (eof() | nl)
options_section = regex(r'options:', re.I) >> optional(nl + indent) >> option_lines << (eof() | nl)

@generate
def doc():
  options = yield many(text ^ options_section)
  usage = yield usage_section
  options += yield many(text ^ options_section)
  return usage, [o for o in options if isinstance(o, Options)]

docopt_lang = doc.parsecmap(splat(DocoptAst))

