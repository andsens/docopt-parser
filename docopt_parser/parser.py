from docopt_parser import DocoptParseError
from functools import reduce
from tests.docopt import DocoptLanguageError
from docopt_parser.parser_utils import char, exclude, explain_error, \
  outer_desc, flatten, join_string, lookahead, splat, string
import re
from parsec import ParseError, eof, generate, many, many1, optional, regex


# TODO:
# Missing the repeated options parser, where e.g. -AA or --opt --opt becomes a counter
# Handle options that are not referenced from usage

nl = char('\n')
whitespaces = many1(char(regex(r'\s'), nl)).parsecmap(join_string).desc('<whitespace>')
eol = optional(whitespaces) + (nl | eof())
indent = (many1(char(' ')) | char('\t')).parsecmap(join_string).desc('<indent> (spaces or tabs)')
multiple = optional(whitespaces) >> string('...').desc('multiplier (...)')

def ident(illegal, starts_with=None):
  if starts_with is None:
    starts_with = char(illegal=illegal)
  return (
    starts_with
    + many(char(illegal=illegal))
  ).parsecmap(flatten).parsecmap(join_string) ^ outer_desc('identifier')


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
  def option_sections(cls):
    re_options_section = regex(r'options:', re.I)
    no_options_text = many(char(illegal=re_options_section)).desc('Text').parsecmap(join_string)

    @generate('options sections')
    def p():
      first_section = yield lookahead(optional(no_options_text >> re_options_section))
      if first_section is not None:
        sections = yield many1(no_options_text >> Option.section() << no_options_text)
        return flatten(sections)
      else:
        return []
    return p

  @classmethod
  def lang(cls):
    no_usage_text = many(char(illegal=regex(r'usage:', re.I))).desc('Text').parsecmap(join_string)

    @generate('docopt help text')
    def p():
      # We need all options before parsing the usage section, so we may need to consume past it
      # before actually parsing it. So the options parsing is a lookahead. In order to fail
      # with a proper error message while parsing the options sections, we reparse everything
      # without the lookahead if the lookahead fails
      options = yield lookahead(cls.option_sections()) ^ cls.option_sections()
      cls.validate_unambiguous_options(options)
      usage = yield (no_usage_text >> Usage.section(options) << no_usage_text)
      return cls(usage, options)
    return p

  @classmethod
  def parse(cls, txt):
    try:
      return cls.lang().parse_strict(txt)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, txt)) from e


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
    illegal = char(' \n')
    first = yield Short.options(illegal) ^ Long.options(illegal)
    if isinstance(first, Long):
      opt_short = yield optional(char(' ,') >> Short.options(illegal))
      opt_long = first
    else:
      opt_short = first
      opt_long = yield optional(char(' ,') >> Long.options(illegal))
    if opt_short is not None and opt_long is not None:
      if opt_short.arg is not None and opt_long.arg is None:
        opt_long.arg = opt_short.arg
      if opt_short.arg is None and opt_long.arg is not None:
        opt_short.arg = opt_long.arg
    return (opt_short, opt_long)


  @classmethod
  def section(cls):
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
        (short, long) = yield cls.opts
        if (yield optional(lookahead(whitespaces + (eof() | nl)))) is not None:
          # Consume trailing whitespaces
          yield whitespaces
        elif (yield optional(lookahead(char(illegal='\n')))) is not None:
          yield (char(' ') + many1(char(' '))) ^ outer_desc('at least 2 spaces')
          doc1 = yield optional(doc)
          _default = yield optional(default)
          doc2 = yield optional(doc)
        options.append(cls(short, long, doc1, _default, doc2))
        if (yield lookahead(optional(next_option))) is None:
          break
        yield nl + indent
      yield eof() | nl
      return options
    return p


class Long(AstNode):
  def __init__(self, name, arg):
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''--{self.name}
  arg: {self.arg}'''

  def usage_parser(self, illegal):
    @generate(f'--{self.name}')
    def p():
      yield string('-' + self.name)
      if self.arg is not None:
        yield (char('=') >> ident(illegal)).desc('argument (=ARG)')
      return self
    return p

  def usage(illegal):
    argument = (char('=') >> Argument.arg).desc('argument')
    return (char('-') >> ident(illegal | char('=')) + optional(argument)) \
        .desc('long option (--long)').parsecmap(splat(Long))

  def options(illegal):
    @generate('long option (--long)')
    def p():
      argument = (char(' =') >> Argument.arg).desc('argument')
      yield string('--')
      name = yield ident(illegal | char('='))
      if (yield optional(lookahead(char('=')))) is not None:
        # Definitely an argument, make sure we fail with "argument expected"
        arg = yield argument
      else:
        arg = yield optional(argument)
      return Long(name, arg)
    return p


class Short(AstNode):
  def __init__(self, name, arg):
    self.name = name
    self.arg = arg

  def __repr__(self):
    return f'''-{self.name}
  arg: {self.arg}'''

  def usage_parser(self, illegal):
    @generate(f'-{self.name}')
    def p():
      yield string(self.name)
      if self.arg is not None:
        yield (optional(char(' ')) >> ident(illegal)).desc('argument ( ARG)')
      return self
    return p

  def usage(illegal):
    argument = (char(' ') >> Argument.arg).desc('argument')
    p = (char(illegal=illegal | char('=-')) + optional(argument)) \
        .desc('short option (-a)').parsecmap(splat(Short))
    return p

  def options(illegal):
    @generate('short option (-s)')
    def p():
      argument = (char(' =') >> Argument.arg).desc('argument')
      yield string('-')
      name = yield ident(illegal | char('=-'))
      if (yield optional(lookahead(char('=')))) is not None:
        # Definitely an argument, make sure we fail with "argument expected"
        arg = yield argument
      else:
        arg = yield optional(argument)
      return Short(name, arg)
    return p


class Usage(object):

  def line(prog, options):
    illegal = char('| \n[(')

    @generate('usage line')
    def p():
      yield string(prog)
      e = yield optional(whitespaces >> expr(illegal, options))
      if e is None:
        e = Sequence([])
      return e
    return p

  def section(options):
    illegal = char('| \n[(')

    @generate('usage section')
    def p():
      yield regex(r'usage:', re.I)
      yield optional(nl + indent)
      prog = yield lookahead(optional(ident(illegal)))
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
def expr(illegal, options):
  @generate('expression')
  def p():
    nodes = [(yield seq(illegal, options))]
    while (yield optional(either)) is not None:
      nodes.append((yield seq(illegal, options)))
    if len(nodes) > 1:
      return Choice(nodes)
    else:
      return nodes[0]
  return p

def seq(illegal, options):
  @generate('sequence')
  def p():
    nodes = [(yield atom(illegal, options))]
    while (yield optional(exclude(whitespaces, either))) is not None:
      nodes.append((yield atom(illegal, options)))
      if (yield optional(lookahead(eol))) is not None:
        yield optional(whitespaces)
        break
    if len(nodes) > 1:
      return Sequence(nodes)
    else:
      return nodes[0]
  return p

def atom(illegal, options):
  excl = illegal | multiple
  # Use | instead of ^ for unambiguous atoms where we *know* that
  # a given starting character *must* be this specific atom. This way
  # we can give useful error messages of what was expected
  return (
    Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
    | Options.options(excl, options)
    | (Argument.arg ^ Command.command(excl) ^ ArgumentSeparator.separator)
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
    return (char('(') >> expr(char('| \n)(['), options) << char(')'))


class Optional(AstNode):
  def __init__(self, item):
    self.item = item

  def __repr__(self):
    return f'''<Optional>
  {self.indent(self.item)}'''

  def new(arg):
    return Optional(arg)

  def optional(options):
    @generate('[optional]')
    def p():
      node = yield (char('[') >> expr(char('| \n][('), options) << char(']'))
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

  def command(illegal):
    starts_with = char(illegal=illegal | char('-'))
    return ident(illegal, starts_with).parsecmap(Command)


class ArgumentSeparator(AstNode):
  def __repr__(self):
    return '<ArgumentSeparator>'

  def new(args):
    return ArgumentSeparator()

  separator = string('--').parsecmap(new)


class Argument(AstNode):
  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return f'''<Argument>: {self.name}'''

  def new(args):
    return Argument(args)

  wrapped_arg = (char('<') + ident(char('\n>')) + char('>')).desc('<arg>').parsecmap(join_string)
  uppercase_arg = regex(r'[A-Z0-9][A-Z0-9-]+').desc('ARG')
  arg = (wrapped_arg ^ uppercase_arg).desc('argument').parsecmap(new)


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

  @classmethod
  def map_references(cls, options, candidates):
    def find(o):
      option = next(filter(lambda opt: o in [opt.short, opt.long], options), None)
      if option is not None:
        return OptionRef(option, o.arg)
      else:
        return o
    return list(map(find, candidates))

  @classmethod
  def options(cls, illegal, options):
    @generate('Options (-s or --long)')
    def p():
      # Check if we should consume, the lookahead checks if this is unambiguously the
      # beginning of an option. This way we can cause atom() to fail with a useful message
      any_option = char('-') + optional(char('-')) + char(illegal=illegal | char('-'))
      yield lookahead(any_option)
      yield char('-')
      known_longs = [o.long.usage_parser(illegal) for o in options if o.long is not None]
      long_p = reduce(lambda mem, p: mem ^ p, known_longs, outer_desc('no --long in Options:'))
      known_shorts = [o.short.usage_parser(illegal) for o in options if o.short is not None]
      short_p = reduce(lambda mem, p: mem ^ p, known_shorts, outer_desc('no --short in Options:'))

      opt = yield long_p | short_p | Long.usage(illegal) | Short.usage(illegal)
      opts = [opt]
      while isinstance(opt, Short) and opt.arg is None:
        opt = yield optional(short_p ^ Short.usage(illegal))
        if opt is None:
          break
        else:
          opts.append(opt)
      return Options(cls.map_references(options, opts))
    return p


class OptionRef(AstNode):
  def __init__(self, option, arg):
    self.option = option
    self.arg = arg

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.option.short or self.option.long)}'''
