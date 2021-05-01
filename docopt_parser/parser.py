from docopt_parser import DocoptParseError
from functools import reduce
from docopt_parser.parser_utils import char, exclude, explain_error, \
  fail_with, flatten, join_string, lookahead, string
import re
from parsec import ParseError, eof, generate, many, many1, optional, regex


# TODO:
# Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
# Handle options that are not referenced from usage
# Indents are optional in both usage: & options:

nl = char('\n')
whitespaces = many1(char(' \t', nl)).parsecmap(join_string).desc('<whitespace>')
eol = optional(whitespaces) + (nl | eof())
indent = (many1(char(' ')) | char('\t')).parsecmap(join_string).desc('<indent> (spaces or tabs)')
multiple = optional(whitespaces) >> string('...').desc('multiplier (...)')
non_symbol_chars = char('=|()[], \t\n\r\b\f\x1B\x07\0') | multiple

def ident(illegal, starts_with=None):
  if starts_with is None:
    starts_with = char(illegal=illegal)
  return (
    starts_with
    + many(char(illegal=illegal))
  ).parsecmap(flatten).parsecmap(join_string) ^ fail_with('identifier')


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

class IdentNode(AstNode):
  def __init__(self, ident):
    super().__init__()
    self.ident = ident

  def __hash__(self):
    return hash(self.ident)


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

  def __repr__(self):
    return f'''<Option>
  short: {self.indent(self.short) if self.short else 'None'}
  long: {self.indent(self.long) if self.long else 'None'}
  arg?:    {self.expects_arg}
  default: {self.default}
  doc:     {self.doc}'''

  @generate('options')
  def opts():
    first = yield Long.options | Short.options
    if isinstance(first, Long):
      opt_short = yield optional((string(', ') | char(' ')) >> Short.options)
      opt_long = first
    else:
      opt_short = first
      opt_long = yield optional((string(', ') | char(' ')) >> Long.options)
    if opt_short is not None and opt_long is not None:
      if opt_short.arg is not None and opt_long.arg is None:
        opt_long.arg = opt_short.arg
      if opt_short.arg is None and opt_long.arg is not None:
        opt_short.arg = opt_long.arg
    return (opt_short, opt_long)


  def section():
    next_option = nl + indent + char('-')
    terminator = (nl + nl) ^ (nl + eof()) ^ next_option
    default = (
      regex(r'\[default: ', re.IGNORECASE) >> many(char(illegal='\n]')) << char(']')
    ).desc('[default: ]').parsecmap(join_string)
    doc = many1(char(illegal=default ^ terminator)).desc('option documentation').parsecmap(join_string)

    @generate('options section')
    def p():
      options = []
      yield regex(r'options:', re.I)
      # TODO: nl + indent is not optional
      yield optional(nl + indent)
      while (yield lookahead(optional(char('-')))) is not None:
        doc1 = _default = doc2 = None
        (short, long) = yield Option.opts
        if (yield optional(lookahead(whitespaces + (eof() | nl)))) is not None:
          # Consume trailing whitespaces
          yield whitespaces
        elif (yield optional(lookahead(char(illegal='\n')))) is not None:
          yield (char(' ') + many1(char(' '))) ^ fail_with('at least 2 spaces')
          doc1 = yield optional(doc)
          _default = yield optional(default)
          doc2 = yield optional(doc)
        options.append(Option(short, long, doc1, _default, doc2))
        if (yield lookahead(optional(next_option))) is None:
          break
        yield nl + indent
      yield eof() | nl
      return options
    return p


class Argument(IdentNode):

  illegal = non_symbol_chars

  def __init__(self, name):
    super().__init__(name)
    self.name = name

  def __repr__(self):
    return f'''<Argument>: {self.name}'''

  def new(args):
    return Argument(args)

  wrapped_arg = (char('<') + ident(illegal | char('>')) + char('>')).desc('<arg>').parsecmap(join_string)

  @generate('ARG')
  def uppercase_arg():
    name_p = many1(char(illegal=Argument.illegal)).parsecmap(join_string).desc('ARG')
    name = yield lookahead(optional(name_p))
    if name is not None and name.isupper():
      name = yield name_p
    else:
      yield fail_with('Not an argument')
    return name

  arg = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(lambda n: Argument(n))


class Long(IdentNode):

  illegal = non_symbol_chars | char(',=')

  def __init__(self, name, arg):
    super().__init__(f'--{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''--{self.name}
  arg: {self.arg}'''

  @property
  def usage_parser(self):
    @generate(f'--{self.name}')
    def p():
      yield string('-' + self.name)
      if self.arg is not None:
        yield (char(' =') >> Argument.arg).desc('argument (=ARG)')
      return self
    return p

  usage = (
    char('-') >> ident(illegal) + optional(char('=') >> Argument.arg)
  ).desc('long option (--long)').parsecmap(lambda n: Long(*n))

  @generate('long option (--long)')
  def options():
    argument = (char(' =') >> Argument.arg).desc('argument')
    yield string('--')
    name = yield ident(Long.illegal)
    if (yield optional(lookahead(char('=')))) is not None:
      # Definitely an argument, make sure we fail with "argument expected"
      arg = yield argument
    else:
      arg = yield optional(argument)
    return Long(name, arg)


class Short(IdentNode):

  illegal = non_symbol_chars | char(',=-')

  def __init__(self, name, arg):
    super().__init__(f'-{name}')
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''-{self.name}
  arg: {self.arg}'''

  @property
  def usage_parser(self):
    @generate(f'-{self.name}')
    def p():
      yield string(self.name).desc(f'-{self.name}')
      if self.arg is not None:
        yield (optional(char(' =')) >> Argument.arg).desc('argument ( ARG)')
      return self
    return p

  usage = (
    char(illegal=illegal) + optional((char(' =') >> Argument.arg))
  ).desc('short option (-a)').parsecmap(lambda n: Short(*n))

  @generate('short option (-s)')
  def options():
    argument = (char(' =') >> Argument.arg).desc('argument')
    yield string('-')
    name = yield char(illegal=Short.illegal)
    if (yield optional(lookahead(char('=')))) is not None:
      # Definitely an argument, make sure we fail with "argument expected"
      arg = yield argument
    else:
      arg = yield optional(argument)
    return Short(name, arg)


class Usage(object):

  def line(prog, options):
    @generate('usage line')
    def p():
      yield string(prog)
      e = yield optional(whitespaces >> expr(options))
      if e is None:
        e = Sequence([])
      return e
    return p

  def section(options):

    @generate('usage section')
    def p():
      yield regex(r'usage:', re.I)
      yield optional(nl + indent)
      prog = yield lookahead(optional(ident(non_symbol_chars)))
      expressions = []
      if prog is not None:
        while True:
          expressions.append((yield Usage.line(prog, options)))
          # consume trailing whitespace
          yield optional(whitespaces)
          if (yield optional(nl + indent)) is None:
            break
      # TODO: must expect two newlines if anything follows
      yield (eof() | nl)
      return Choice(expressions)
    return p


either = (many(char(' ')) >> char('|') << many(char(' '))).desc('<pipe> (|)')
def expr(options):
  @generate('expression')
  def p():
    nodes = [(yield seq(options))]
    while (yield optional(either)) is not None:
      nodes.append((yield seq(options)))
    if len(nodes) > 1:
      return Choice(nodes)
    else:
      return nodes[0]
  return p

def seq(options):
  @generate('sequence')
  def p():
    nodes = [(yield atom(options))]
    while (yield optional(exclude(whitespaces, either))) is not None:
      nodes.append((yield atom(options)))
      if (yield optional(lookahead(eol))) is not None:
        yield optional(whitespaces)
        break
    if len(nodes) > 1:
      return Sequence(nodes)
    else:
      return nodes[0]
  return p

def atom(options):
  # Use | instead of ^ for unambiguous atoms where we *know* that
  # a given starting character *must* be this specific atom. This way
  # we can give useful error messages of what was expected
  return (
    Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
    | ArgumentSeparator.separator | Options.options(options)
    | Argument.arg | Command.command
  ).bind(Multiple.multi).desc('atom')


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
    return (char('(') >> expr(options) << char(')'))


class Optional(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f'''<Optional>
{self.indent(self.items)}'''

  def new(arg):
    return Optional(arg)

  def optional(options):
    @generate('[optional]')
    def p():
      node = yield (char('[') >> expr(options) << char(']'))
      if isinstance(node, (Optional, Sequence)):
        return Optional(node.items)
      else:
        return Optional([node])
    return p


class Command(IdentNode):
  illegal = non_symbol_chars

  def __init__(self, name):
    super().__init__(name)
    self.name = name

  def __repr__(self):
    return f'''<Command>: {self.name}'''

  command = ident(illegal, starts_with=char(illegal=illegal | char('-'))).parsecmap(lambda n: Command(n))


class ArgumentSeparator(AstNode):
  def __repr__(self):
    return '<ArgumentSeparator>'

  def new(args):
    return ArgumentSeparator()

  separator = (lookahead(string('--') << char('| \n)()[]') | nl | eof()) >> string('--')).parsecmap(new)


class OptionsShortcut(AstNode):
  def __repr__(self):
    return '<OptionsShortcut>'

  def new(args):
    return OptionsShortcut()

  shortcut = string('options').parsecmap(new)


class Options(AstNode):
  def __init__(self, options):
    self.options = options

  def __repr__(self):
    return f'''<Options>
{self.indent(self.options)}'''

  def map_references(options, candidates):
    def find(o):
      option = next(filter(lambda opt: o in [opt.short, opt.long], options), None)
      if option is not None:
        return OptionRef(option, o.arg)
      else:
        return o
    return list(map(find, candidates))

  def options(options):
    @generate('Options (-s or --long)')
    def p():
      # Check if we should consume, the lookahead checks if this is unambiguously the
      # beginning of an option. This way we can cause atom() to fail with a useful message
      any_option = char('-') + optional(char('-')) + char(illegal=non_symbol_chars | char('-'))
      yield lookahead(any_option)
      yield char('-')
      known_longs = [o.long.usage_parser for o in options if o.long is not None]
      long_p = reduce(lambda mem, p: mem ^ p, known_longs, fail_with('no --long in Options:'))
      known_shorts = [o.short.usage_parser for o in options if o.short is not None]
      short_p = reduce(lambda mem, p: mem ^ p, known_shorts, fail_with('no -s in Options:'))

      opt = yield long_p | short_p | Long.usage | Short.usage
      opts = [opt]
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(short_p ^ Short.usage)
        if opt is None:
          break
        else:
          opts.append(opt)
      return Options(Options.map_references(options, opts))
    return p


class OptionRef(AstNode):
  def __init__(self, option, arg):
    self.option = option
    self.arg = arg

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.option.short or self.option.long)}'''


class DocoptAst(AstNode):
  def __init__(self, usage, options_sections):
    self.usage = usage
    self.options_sections = options_sections

  def __repr__(self):
    options = '\n'.join([f'''  options:
{self.indent(section, 2)}''' for section in self.options_sections])
    return f'''<Docopt>
  usage:
{self.indent([self.usage], 2)}
{options}'''

  def validate_unambiguous_options(options):
    shorts = [getattr(o.short, 'name') for o in options if o.short is not None]
    longs = [getattr(o.long, 'name') for o in options if o.long is not None]
    dup_shorts = set([n for n in shorts if shorts.count(n) > 1])
    dup_longs = set([n for n in longs if longs.count(n) > 1])
    messages = \
        ['-%s is specified %d times' % (n, shorts.count(n)) for n in dup_shorts] + \
        ['--%s is specified %d times' % (n, longs.count(n)) for n in dup_longs]
    if len(messages):
      raise DocoptParseError(', '.join(messages))

  re_options_section = regex(r'options:', re.I)
  no_options_text = many(char(illegal=re_options_section)).desc('Text').parsecmap(join_string)

  @generate
  def options_sections():
    sections = []
    yield DocoptAst.no_options_text
    while (yield lookahead(optional(DocoptAst.re_options_section))) is not None:
      sections.append((yield Option.section() << DocoptAst.no_options_text))
    return sections

  no_usage_text = many(char(illegal=regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)

  @generate('docopt help text')
  def lang():
    options_sections = yield lookahead(DocoptAst.options_sections) ^ DocoptAst.options_sections
    options = flatten(options_sections)
    DocoptAst.validate_unambiguous_options(options)
    usage = yield (DocoptAst.no_usage_text >> Usage.section(options) << DocoptAst.no_usage_text)
    return DocoptAst(usage, options_sections)

  def parse(txt, strict=True):
    try:
      if strict:
        return DocoptAst.lang.parse_strict(txt)
      else:
        return DocoptAst.lang.parse(txt)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e
