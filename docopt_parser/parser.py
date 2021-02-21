from functools import reduce
from tests.docopt import DocoptLanguageError
from docopt_parser.parser_utils import exclude, flatten, join_string, splat
import re
from parsec import eof, generate, many, many1, none_of, one_of, optional, regex, sepBy, sepBy1, string

char = regex(r'.|\n').desc('any char')
not_nl = none_of('\n').desc('*not* <newline>')
tab = string('\t').desc('<tab>')
space = string(' ').desc('<space>')
whitespace = regex(r'\s').desc('<whitespace>')
indent = many1(space) | tab
nl = string('\n').desc('<newline>')
either = (many(space) >> string('|') << many(space)).desc('<pipe> (|)')
multiple = string('...').desc('multiplier (...)')

def symbol_char(excludes):
  return exclude(char, excludes)

def symbol(excludes):
  return many1(symbol_char(excludes)).desc('symbol').parsecmap(''.join)


class AstNode(object):
  def __init__(self):
    pass

  def indent(self, node, lvl=1):
    if isinstance(node, list):
      lines = '\n'.join(map(repr, node)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
    else:
      lines = repr(node).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)


class DocoptAst(AstNode):
  def __init__(self, usage, options):
    self.usage = usage
    self.options = flatten(options)

  def __repr__(self):
    return f'''<Docopt>
  usage:
{self.indent([self.usage], 2)}
  options:
{self.indent(self.options, 2)}'''

  @classmethod
  def validate_unambiguous_options(cls, options):
    shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
    longs = [getattr(o.long, 'name') for o in options if o.long is not None]
    dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
    dup_longs = set([n for n in longs if longs.count(n) > 1])
    messages = \
        ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
        ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
    if len(messages):
      raise DocoptLanguageError(', '.join(messages))

  @classmethod
  def parse(cls, txt):
    no_options_text = many1(exclude(char, regex(r'options:', re.I))).desc('Text').parsecmap(join_string)
    parsed = many(no_options_text ^ Option.section).parse_strict(txt)
    options = flatten([o for o in parsed if isinstance(o, list)])
    cls.validate_unambiguous_options(options)
    no_usage_text = many1(exclude(char, regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)
    usage = (no_usage_text >> Usage.section(options) << no_usage_text).parse_strict(txt)
    return cls(usage, options)


class Option(AstNode):

  def __init__(self, short, long, doc1, default=None, doc2=None):
    super().__init__()
    self.short = short
    self.long = long
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.default = default
    self.doc = ''.join(t for t in [
      '' if doc1 is None else doc1,
      '' if default is None else f'[default: {default}]',
      '' if doc2 is None else doc2,
    ])

  def new(args):
    return Option(*args)

  def __repr__(self):
    return f'''<Option>
  short: {self.indent(self.short) if self.short else 'None'}
  long: {self.indent(self.long) if self.long else 'None'}
  arg?:    {self.expects_arg}
  default: {self.default}
  doc:     {self.doc}'''

  @generate('options')
  def opts():
    exclude = one_of(' \n')
    first = yield Short.short(exclude) ^ Long.long(exclude)
    if isinstance(first, Long):
      opt_short = yield optional(many1(one_of(' ,')) >> Short.short(exclude))
      opt_long = first
    else:
      opt_short = first
      opt_long = yield optional(many1(one_of(' ,')) >> Long.long(exclude))
    if opt_short is not None and opt_long is not None:
      if opt_short.arg is not None and opt_long.arg is None:
        opt_long.arg = opt_short.arg
      if opt_short.arg is None and opt_long.arg is not None:
        opt_short.arg = opt_long.arg
    return (opt_short, opt_long)

  default = (
    regex(r'\[default: ', re.IGNORECASE) >> many(none_of('\n]')) << string(']')
  ).desc('[default: ]').parsecmap(join_string)
  terminator = (nl + nl) ^ (nl + eof()) ^ (nl + indent + string('-'))
  doc = many1(exclude(char, default ^ terminator)).desc('option documentation').parsecmap(join_string)
  desc = (optional(doc) + optional(default) + optional(doc)).parsecmap(flatten)
  line = (opts + optional(space + many1(space) >> desc)).desc('option line').parsecmap(flatten).parsecmap(new)

  option_lines = sepBy(line, nl + indent)
  section = regex(r'options:', re.I) >> optional(nl + indent) >> option_lines << (eof() | nl)


class Long(AstNode):
  def __init__(self, name, arg):
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''--{self.name}
  arg: {self.arg}'''

  def usage_parser(self, excludes):
    @generate(f'--{self.name}')
    def p():
      yield string('-')
      yield string(self.name)
      if self.arg is not None:
        yield string('=')
        yield symbol(excludes)
      return self
    return p

  def long(excludes):
    return (string('--') >> symbol(excludes | string('=')) + optional(one_of(' =') >> Argument.arg)) \
      .desc('long option (--long)').parsecmap(splat(Long))


class Short(AstNode):
  def __init__(self, name, arg):
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''-{self.name}
  arg: {self.arg}'''

  def usage_parser(self, excludes):
    @generate(f'-{self.name}')
    def p():
      yield string(self.name)
      if self.arg is not None:
        yield optional(space)
        yield symbol(excludes)
      return self
    return p

  def short(excludes):
    return (string('-') >> symbol_char(excludes | one_of('=-')) + optional(one_of(' =') >> Argument.arg)) \
      .desc('short option (-a)').parsecmap(splat(Short))


class Usage(object):
  def usage_lines(options):
    @generate('usage lines')
    def p():
      excludes = one_of('| \n[(')
      prog = yield symbol(excludes)
      yield many(whitespace)
      expressions = [(yield expr(excludes, options))]
      yield many(whitespace)
      expressions += yield sepBy(string(prog) << many(whitespace) >> expr(excludes, options), nl + indent)
      return Choice(expressions)
    return p

  @classmethod
  def section(cls, options):
    return regex(r'usage:', re.I) >> optional(nl + indent) >> cls.usage_lines(options) << (eof() | nl)


def expr(excludes, options):
  @generate('expression')
  def p():
    nodes = yield sepBy1(seq(excludes, options), either)
    if len(nodes) > 1:
      return Choice(nodes)
    else:
      return nodes[0]
  return p

def seq(excludes, options):
  @generate('sequence')
  def p():
    nodes = yield sepBy1(atom(excludes, options), exclude(whitespace, nl))
    if len(nodes) > 1:
      return Sequence(nodes)
    else:
      return nodes[0]
  return p

def atom(excludes, options):
  @generate('atom')
  def p():
    excl = excludes | multiple
    a = yield (
      Group.group(options) ^ Optional.opt(options) ^ OptionsShortcut.shortcut
      ^ UsageOptions.options(excl, options)
      ^ Argument.arg ^ Command.command(excl)
    ).bind(Multiple.multi)
    return a
  return p


class Multiple(AstNode):
  def __init__(self, item):
    self.item = item

  def __repr__(self):
    return f'''<Multiple>: {self.item}'''

  def multi(of):
    return optional(multiple).parsecmap(lambda m: Multiple(of) if m else of)


class Choice(AstNode):
  def __init__(self, items):
    if len(items) > 1:
      new_items = []
      for item in items:
        if isinstance(item, Choice):
          new_items += item.items
        else:
          new_items.append(item)
      self.items = new_items
    else:
      self.items = items

  def __repr__(self):
    return f'''<Choice>
{self.indent(self.items)}'''


class Sequence(AstNode):
  def __init__(self, items):
    self.items = items
    if len(items) > 1:
      new_items = []
      for item in items:
        if isinstance(item, Sequence):
          new_items += item.items
        else:
          new_items.append(item)
      self.items = new_items
    else:
      self.items = items

  def __repr__(self):
    return f'''<Sequence>
{self.indent(self.items)}'''


class Group(object):
  def group(options):
    return (string('(') >> expr(one_of('| \n)(['), options) << string(')')).desc('(group)')


class Optional(AstNode):
  def __init__(self, item):
    self.item = item

  def __repr__(self):
    return f'''<Optional>
  {self.indent(self.item)}'''

  def new(arg):
    return Optional(arg)

  def opt(options):
    @generate('[optional]')
    def p():
      node = yield (string('[') >> expr(one_of('| \n][('), options) << string(']'))
      if isinstance(node, Optional):
        return Optional(node.item)
      else:
        return Optional(node)
    return p


class Command(AstNode):
  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return f'''<Command>: {self.name}'''

  def command(excludes):
    return symbol(excludes).desc('command').parsecmap(Command)


class Argument(AstNode):
  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return f'''<Argument>: {self.name}'''

  def new(args):
    return Argument(args)

  wrapped_arg = (string('<') + symbol(string('>')) + string('>')).desc('<ARG>').parsecmap(join_string)
  uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]+').desc('ARG')
  arg = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(new)


class OptionsShortcut(AstNode):
  def __repr__(self):
    return '''<OptionsShortcut>'''

  def new(args):
    return OptionsShortcut()

  shortcut = string('options').parsecmap(new)


class UsageOptions(AstNode):
  def __init__(self, names, arg):
    self.names = names
    self.arg = arg

  def __repr__(self):
    return f'''<UsageOptions>
  arg: {self.arg}
{self.indent(self.names)}'''

  def options(excludes, options):
    @generate('Options (-s or --long)')
    def p():
      known_longs = [o.long.usage_parser(excludes) for o in options if o.long is not None]
      long_p = reduce(lambda mem, p: mem ^ p, known_longs)
      known_shorts = [o.short.usage_parser(excludes) for o in options if o.short is not None]
      short_p = reduce(lambda mem, p: mem ^ p, known_shorts)
      yield string('-')
      opt = yield long_p ^ short_p
      opts = [opt]
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(short_p)
        if opt is None:
          break
        else:
          opts.append(opt)
      return opts
    return p
