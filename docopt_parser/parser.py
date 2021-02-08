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
  def construct(res):
    if isinstance(res, Node):
      res = [res]
    return Node(node_type, res)
  return construct


class Node(namedtuple('Node', ['type', 'children'])):

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
    return '{indent}<{type}>{children}'.format(indent=' ' * indent, type=self.type, children=children)

  def __str__(self):
    return self.toString()


def section_title(title):
  return regex(re.escape(title) + ':', re.IGNORECASE)


@generate
def atom():
  return (yield group ^ opt ^ options_shortcut ^ long ^ shorts ^ arg ^ command)


any = regex('.').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
symbol_char = regex(r'[^\s|()\[\]<>=]*')
symbol = (regex(r'[^\s|()\[\]<>=-]') + symbol_char).parsecmap(''.join)
either = (string('|') ^ (space >> string('|'))) << optional(space)
rest_of_line = many(not_nl).desc('rest of the line').parsecmap(''.join)
wrapped_arg = string('<') >> symbol << string('>').parsecmap(to_node('<arg>'))
uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]*').parsecmap(to_node('ARG'))
arg = (wrapped_arg ^ uppercase_arg).parsecmap(to_node('argument'))
program = symbol.parsecmap(to_node('program'))
long = (string('--') >> symbol + optional(regex(r' |=') >> arg)).parsecmap(to_node('--long'))
shorts = (string('-') >> symbol_char + optional(space >> arg)).parsecmap(to_node('-s'))
command = symbol.parsecmap(to_node('command'))
options_shortcut = string('options').parsecmap(to_node('options shortcut'))
multiple = string('...').parsecmap(to_node('multiple'))
seq = sepBy(atom + multiple ^ atom, space).parsecmap(to_node('seq'))
expr = sepBy(seq, either).parsecmap(to_node('expr either'))
group = (string('(') >> expr << string(')')).parsecmap(to_node('group'))
opt = (string('[') >> expr << string(']')).parsecmap(to_node('optional'))
usage_expression = (program << space >> expr)
usage_lines = sepBy(usage_expression, nl + indent).parsecmap(to_node('usage lines'))
usage_section = optional(nl + indent) >> usage_lines << (eof() | nl)
usage_title = section_title('usage').desc('"Usage:" section').parsecmap(to_node('usage title'))
preamble = (exclude(rest_of_line, usage_title) << nl).desc('Preamble').parsecmap(to_node('preamble'))


@generate
def doc():
  return [(yield preamble), (yield usage_title), (yield usage_section)]


docopt_lang = doc.parsecmap(to_node('docopt_lang'))
