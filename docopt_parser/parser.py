from collections import namedtuple
from docopt_parser import DocoptParseError
import re
from parsec import ParseError, Parser, Value, eof, generate, many, many1, none_of, optional, regex, sepBy, string

def parse(doc):
  try:
    return docopt_lang.parse_strict(doc)
  except ParseError as e:
    line_no, col = e.loc_info(e.text, e.index)
    line = doc.split('\n')[line_no]
    msg = '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))
    raise DocoptParseError(msg) from None

def exclude(p, end):
  '''Fails parser p if parser end matches
  '''
  @Parser
  def exclude_parser(text, index):
    res = end(text, index)
    if res.status:
      return Value.failure(index, 'did not expect ' + res.value)
    else:
      return p(text, index)
  return exclude_parser

def to_node(node_type):
  def construct(res, name=None):
    if isinstance(res, Node):
      res = [res]
    return Node(node_type, name, res)
  return construct


class Node(namedtuple('Node', ['type', 'name', 'children'])):

  def childToString(self, child, indent):
    if isinstance(child, Node):
      return child.toString(indent + 2)
    else:
      return '{indent}{type}: {str}'.format(indent=(' ' * (indent + 2)), type=str(type(child)), str=str(child))

  def toString(self, indent=0):
    if type(self.children) is list:
      children = '\n' + '\n'.join([self.childToString(c, indent + 2) for c in self.children])
    else:
      children = ' "{str}"'.format(str=str(self.children))
    if self.name:
      return '{indent}{type} <{name}>{children}'.format(
        indent=' ' * indent, type=self.type, name=self.name, children=children)
    else:
      return '{indent}{type}{children}'.format(indent=' ' * indent, type=self.type, children=children)

  def __str__(self):
    return self.toString()

def symbol_char(disallowed):
  return none_of('| \n' + disallowed)

def symbol(disallowed):
  return many1(symbol_char(disallowed)).parsecmap(''.join)

def atom(disallowed):
  @generate
  def p():
    node = yield group ^ opt ^ options_shortcut ^ long(disallowed) ^ shorts(disallowed) ^ arg ^ command(disallowed)
    mult = yield optional(multiple)
    if mult is not None:
      return to_node('multiple')(node)
    else:
      return node
  return p

def long(disallowed):
  @generate
  def p():
    yield string('--')
    name = yield symbol(disallowed + '=')
    arg_node = yield optional(regex(r' |=') >> arg)
    return to_node('--long')(arg_node, name=name)
  return p

def shorts(disallowed):
  @generate
  def p():
    yield string('-')
    name = yield symbol_char(disallowed + '=')
    arg_node = yield optional(space >> arg)
    return to_node('-s')(arg_node, name=name)
  return p

def command(disallowed):
  return symbol(disallowed).parsecmap(to_node('command'))

def seq(disallowed):
  return sepBy(atom(disallowed), exclude(whitespace, nl)).parsecmap(to_node('seq'))

def expr(disallowed):
  return sepBy(seq(disallowed), either).parsecmap(to_node('expr'))

@generate
def group():
  return (yield (string('(') >> expr(')') << string(')')).parsecmap(to_node('group')))

@generate
def opt():
  return (yield (string('[') >> expr(']') << string(']')).parsecmap(to_node('optional')))

def section_title(title_re):
  return regex(r'(%s):' % title_re, re.IGNORECASE)

any = regex(r'.|\n').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
whitespace = regex(r'\s').desc('<whitespace>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
multiple = string('...').parsecmap(to_node('multiple'))
either = (string('|') ^ (space >> string('|'))) << optional(space)
wrapped_arg = (string('<') >> symbol('>') << string('>')).parsecmap(to_node('<arg>'))
uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]*').parsecmap(to_node('ARG'))
arg = (wrapped_arg ^ uppercase_arg)
options_shortcut = string('options').parsecmap(to_node('options shortcut'))

@generate
def usage_lines():
  prog = yield symbol('')
  yield many(whitespace)
  expressions = [(yield expr(''))]
  yield many(whitespace)
  expressions += yield sepBy(string(prog) << many(whitespace) >> expr(''), nl + indent)
  return Node('usage_lines', None, expressions)

text = many1(
  exclude(any, section_title('usage|options'))).desc('Text').parsecmap(lambda c: to_node('text')(''.join(c)))

# option_lines = sepBy(option_line, nl + indent).parsecmap(to_node('usage lines'))

usage_section = section_title('usage') >> optional(nl + indent) >> usage_lines << (eof() | nl)
# options_section = section_title('options') >> optional(nl + indent) >> option_lines << (eof() | nl)

# \n[ \t]*(-\S+?)

# # FIXME corner case "bla: options: --foo"
# _, _, s = s.partition(':')  # get rid of "options:"
# split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:]
# split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
# options = [Option.parse(s) for s in split if s.startswith('-')]
# defaults += options

@generate
def doc():
  non_usage = yield many(text)
  usage = yield usage_section
  non_usage += yield many(text)
  return [usage] + non_usage

docopt_lang = doc.parsecmap(to_node('docopt_lang'))
