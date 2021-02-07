from collections import namedtuple
from functools import reduce
import re
from parsec import Parser, Value, eof, generate, many, many1, none_of, optional, regex, sepBy, string


def section_title(title):
  return regex(re.escape(title) + ':', re.IGNORECASE)


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


any = regex('.').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
rest_of_line = many(not_nl).desc('rest of the line').parsecmap(''.join)
usage_title = section_title('usage').desc('"Usage:" section')
preamble = (exclude(rest_of_line, usage_title) << nl).desc('Preamble')


@generate
def docopt():
  ast = {}
  ast['preamble'] = yield preamble
  yield usage_title
  ast['usage'] = yield usage_section
  return ast


@generate
def usage_section():
  yield optional(nl + indent)
  nodes = yield usage_lines
  yield nl | eof()

  return nodes


@generate
def expression():
  line = yield many(exclude(any, nl | eof())).parsecmap(''.join)
  return [line]


usage_lines = sepBy(expression, nl + indent).parsecmap(
  lambda lists: Node('either', reduce(lambda rem, l: rem + l, lists, []))
)


class Node(namedtuple('Node', ['type', 'children'])):
  pass

"""atom ::= '(' expr ')' | '[' expr ']' | 'options'
        | long | shorts | argument | command ;
"""
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
