from collections import namedtuple
from docopt_parser import DocoptParseError
import re
from .parsec import ParseError, Parser, Value, eof, generate, many, many1, none_of, one_of, optional, regex, sepBy, sepBy1, string

def parse(doc):
  try:
    return docopt_lang.parse_strict(doc)
  except ParseError as e:
    raise DocoptParseError(explain_error(e, doc)) from None

def explain_error(e, text):
  line_no, col = e.loc_info(e.text, e.index)
  line = text.split('\n')[line_no]
  return '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))

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

def to_node(node_type):
  def construct(children, name=None):
    if isinstance(children, Node):
      children = [children]
    return Node(node_type, name, children)
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
    elif self.children is not None:
      children = ' "{str}"'.format(str=str(self.children))
    else:
      children = ''
    if self.name:
      return '{indent}{type} <{name}>{children}'.format(
        indent=' ' * indent, type=self.type, name=self.name, children=children)
    else:
      return '{indent}{type}{children}'.format(indent=' ' * indent, type=self.type, children=children)

  def __str__(self):
    return self.toString()

def symbol_char(excludes):
  return exclude(any, excludes)

def symbol(excludes):
  return many1(symbol_char(excludes)).parsecmap(''.join)

def atom(excludes):
  excludes = excludes | multiple

  @generate
  def p():
    node = yield group(excludes) ^ opt(excludes) ^ options_shortcut ^ long(excludes) ^ shorts(excludes) ^ arg ^ command(excludes)
    mult = yield optional(multiple)
    if mult is not None:
      return to_node('multiple')(node)
    else:
      return node
  return p

def long(excludes):
  @generate
  def p():
    yield string('--')
    name = yield symbol(excludes | string('='))
    arg_node = yield optional(one_of(' =') >> arg)
    if arg_node:
      arg_node = [arg_node]
    return Node('--long', name, arg_node)
  return p

def short(excludes):
  @generate
  def p():
    yield string('-')
    name = yield symbol_char(excludes | string('='))
    arg_node = yield optional(space >> arg)
    if arg_node:
      arg_node = [arg_node]
    return Node('-s', name, arg_node)
  return p

def shorts(excludes):
  # TODO: Handle multiple shorts
  return short(excludes)

def command(excludes):
  return symbol(excludes).parsecmap(to_node('command'))

def seq(excludes):
  return sepBy(atom(excludes), exclude(whitespace, nl)).parsecmap(to_node('seq'))

def expr(excludes):
  return sepBy(seq(excludes), either).parsecmap(to_node('expr'))

def group(excludes):
  @generate
  def p():
    # Need to inherit disallowed here, but be able to remove invalid ones
    return (yield (string('(') >> expr(excludes | string(')')) << string(')')).parsecmap(to_node('group')))
  return p

def opt(excludes):
  @generate
  def p():
    # Need to inherit disallowed here, but be able to remove invalid ones
    return (yield (string('[') >> expr(excludes | string(']')) << string(']')).parsecmap(to_node('optional')))
  return p

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
either = many(space) >> string('|') << many(space)
wrapped_arg = (string('<') >> symbol(string('>')) << string('>')).parsecmap(to_node('<arg>'))
uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]+').parsecmap(to_node('ARG'))
arg = (wrapped_arg ^ uppercase_arg)
options_shortcut = string('options').parsecmap(to_node('options shortcut'))

@generate
def usage_lines():
  excludes = one_of('| \n')
  prog = yield symbol(excludes)
  yield many(whitespace)
  expressions = [(yield expr(excludes))]
  yield many(whitespace)
  expressions += yield sepBy(string(prog) << many(whitespace) >> expr(excludes), nl + indent)
  return Node('usage_lines', None, expressions)

@generate
def option_line():
  excludes = one_of(' \n')
  nodes = yield sepBy1(long(excludes) ^ short(excludes), one_of(' ,'))
  yield space + many1(space)
  desc = yield optional(many(exclude(any, (nl + nl) ^ (nl + eof()) ^ (nl + indent + string('-')))).parsecmap(
    lambda c: to_node('text')(''.join(c))))
  return Node('option line', '', nodes + [desc])

text = many1(
  exclude(any, section_title('usage|options'))).desc('Text').parsecmap(lambda c: to_node('text')(''.join(c)))

option_lines = sepBy(option_line, nl + indent).parsecmap(to_node('option lines'))
usage_section = section_title('usage') >> optional(nl + indent) >> usage_lines << (eof() | nl)
options_section = section_title('options') >> optional(nl + indent) >> option_lines << (eof() | nl)

@generate
def doc():
  nodes = yield many(text ^ options_section)
  nodes.append((yield usage_section))
  nodes += yield many(text ^ options_section)
  return nodes

docopt_lang = doc.parsecmap(to_node('docopt_lang'))
