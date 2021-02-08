from collections import namedtuple
from docopt_parser import DocoptParseError
import re
from parsec import ParseError, Parser, Value, eof, generate, many, many1, none_of, optional, regex, sepBy, string


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
      children = ' ' + str(self.children)
    return '{indent}<{type}>{children}'.format(indent=' ' * indent, type=self.type, children=children)

  def __str__(self):
    return self.toString()


def parse(doc):
  try:
    return docopt_lang.parse_strict(doc)
  except ParseError as e:
    line_no, col = e.loc_info(e.text, e.index)
    line = doc.split('\n')[line_no]
    msg = '\n{line}\n{col}^\n{msg}'.format(line=line, col=' ' * col, msg=str(e))
    raise DocoptParseError(msg) from None


def req(p):
  @generate
  def req_expr():
    return (yield string('(') >> p.parsecmap(to_node('req_expr')) << string(')'))
  return req_expr


def opt(p):
  @generate
  def opt_expr():
    return (yield string('[') >> p.parsecmap(to_node('opt_expr')) << string(']'))
  return opt_expr


@generate
def atom():
  """atom ::= '(' expr ')' | '[' expr ']' | 'options'
            | long | shorts | argument | command ;"""
  atom = yield req(expr) ^ opt(expr) ^ options_shortcut ^ long ^ shorts ^ arg ^ command
  return atom


def section_title(title):
  return regex(re.escape(title) + ':', re.IGNORECASE)


any = regex('.').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
rest_of_line = many(not_nl).desc('rest of the line').parsecmap(''.join)
wrapped_arg = string('<') >> regex(r'([^\>\s])+') << string('>')
uppercase_arg = regex(r'[A-Z0-9]+')
arg = (wrapped_arg ^ uppercase_arg).parsecmap(to_node('argument'))
program = regex(r'\S+').parsecmap(to_node('program'))
long = string('--') + regex(r'(\S|[^=])+') + optional(regex(' |=') + regex(r'\S+'))
shorts = string('-') + regex(r'[^-]\S+') + optional(regex(' ') + regex(r'\S+'))
command = regex(r'\S+').parsecmap(to_node('command'))
options_shortcut = string('options')
multiple = string('...').parsecmap(to_node('multiple'))
seq = sepBy(atom + multiple ^ atom, space).parsecmap(to_node('seq'))
expr = sepBy(seq, string('|')).parsecmap(to_node('expr either'))
usage_expression = (program << space >> expr)
usage_lines = sepBy(usage_expression, nl + indent).parsecmap(to_node('usage_lines either'))
usage_section = optional(nl + indent) >> usage_lines << (eof() | nl)
usage_title = section_title('usage').desc('"Usage:" section').parsecmap(to_node('usage_title'))
preamble = (exclude(rest_of_line, usage_title) << nl).desc('Preamble').parsecmap(to_node('preamble'))


@generate
def doc():
  return [(yield preamble), (yield usage_title), (yield usage_section)]


docopt_lang = doc.parsecmap(to_node('docopt_lang'))

# '''
# ^(
#   [^\n]*
#   usage:
#   [^\n]*
#   \n?
#   (?:
#     [ \t]
#     .*?
#     (?:\n|$)
#   )*
# )
# '''
# usage_sections = parse_section('usage:', doc)
# if len(usage_sections) == 0:
#     raise DocoptLanguageError('"usage:" (case-insensitive) not found.')
# if len(usage_sections) > 1:
#     raise DocoptLanguageError('More than one "usage:" (case-insensitive).')
# DocoptExit.usage = usage_sections[0]

# options = parse_defaults(doc)
# pattern = parse_pattern(formal_usage(DocoptExit.usage), options)
# # [default] syntax for argument is disabled
# #for a in pattern.flat(Argument):
# #    same_name = [d for d in arguments if d.name == a.name]
# #    if same_name:
# #        a.value = same_name[0].value
# argv = parse_argv(Tokens(argv), list(options), options_first)
# pattern_options = set(pattern.flat(Option))
# for options_shortcut in pattern.flat(OptionsShortcut):
#     doc_options = parse_defaults(doc)
#     options_shortcut.children = list(set(doc_options) - pattern_options)
#     #if any_options:
#     #    options_shortcut.children += [Option(o.short, o.long, o.argcount)
#     #                    for o in argv if type(o) is Option]
# extras(help, version, argv, doc)
# matched, left, collected = pattern.fix().match(argv)
# if matched and left == []:  # better error message if left?
#     return Dict((a.name, a.value) for a in (pattern.flat() + collected))
# raise DocoptExit()


# def parse_section(name, source):
def parse_section(name):
  return regex('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)', re.IGNORECASE | re.MULTILINE)
#     pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
#                          re.IGNORECASE | re.MULTILINE)
#     return [s.strip() for s in pattern.findall(source)]

# def parse_defaults(doc):
#     defaults = []
#     for s in parse_section('options:', doc):
#         # FIXME corner case "bla: options: --foo"
#         _, _, s = s.partition(':')  # get rid of "options:"
#         split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:]
#         split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
#         options = [Option.parse(s) for s in split if s.startswith('-')]
#         defaults += options
#     return defaults
