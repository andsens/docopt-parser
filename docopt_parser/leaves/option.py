from functools import reduce
import typing as T
import parsec as P

from docopt_parser import base, leaves, groups
from docopt_parser.util import helpers, marks, parsers

class Option(base.Leaf):
  definition: "Option"
  __arg: "leaves.Argument | None"
  __short_alias: "marks.Marked[str] | None"
  __default: "marks.Marked[str] | None"
  __doc: "marks.Marked[str] | None"
  __is_definition: bool

  def __init__(self, name: marks.MarkedTuple[str], arg: "leaves.Argument | None", definition: "Option | None" = None,
               short_alias: "marks.MarkedTuple[str] | None" = None,
               default: "marks.MarkedTuple[str] | None" = None, doc: "marks.MarkedTuple[str] | None" = None):
    super().__init__(name)
    self.__arg = arg
    self.definition = definition or self
    self.__is_definition = definition is None
    self.__short_alias = marks.Marked(short_alias) if short_alias else None
    self.__default = marks.Marked(default) if default else None
    self.__doc = marks.Marked(doc) if doc else None

  @property
  def default(self) -> "T.List[str] | str | None | T.Literal[0] | T.Literal[False]":
    if self.arg and self.multiple:
      return self.definition.__default.elm.split(' ') if self.definition.__default else []
    elif self.arg:
      return self.definition.__default.elm if self.definition.__default else None
    elif self.multiple:
      return 0
    else:
      return False

  @property
  def doc(self):
    return self.definition.__doc.elm if self.definition.__doc else None

  @property
  def short_alias(self):
    return self.definition.__short_alias.elm if self.definition.__short_alias else None

  @property
  def arg(self):
    return self.__arg or self.definition.__arg

  def __repr__(self):
    arg_suffix = ' ' + self.arg.ident if self.arg else ''
    return f'{self.ident}{self.multiple_suffix}{arg_suffix}'

  def __iter__(self):
    yield from super().__iter__()
    if not self.__is_definition:
      yield 'definition', self.definition.dict
    else:
      if self.default:
        yield 'default', self.default
      if self.doc:
        yield 'doc', self.doc
    if self.arg:
      yield 'arg', self.arg.dict

  def __hash__(self) -> int:
    return hash(self.definition.ident)

  def __eq__(self, other: T.Any) -> bool:
    return isinstance(other, Option) and self.definition.ident == other.definition.ident

  @property
  def atom_parser(self):
    if self.ident.startswith('--'):
      # The lookahead is to ensure that we don't consume a prefix of another option
      # e.g. --ab matching --abc
      name_p = P.unit(parsers.string(self.ident) << P.lookahead(long_illegal)).mark()
      arg_p = parsers.char(' =') >> leaves.option_argument
    else:
      name_p = parsers.string(self.ident).mark()
      arg_p = P.optional(parsers.char(' =')) >> leaves.option_argument
    if self.arg:
      return (name_p + arg_p.desc('argument')).parsecmap(lambda n: Option(*n, self.definition))
    else:
      return (
        name_p << P.optional(
          P.lookahead(parsers.char('=') + parsers.throw(f'{self.ident} does not expect an argument'))
        )
      ).parsecmap(lambda n: Option(n, None, self.definition))

  @property
  def atom_parser_shortlist(self):
    if self.ident.startswith('--'):
      return None
    name_p = parsers.string(self.ident[1]).mark()
    if self.arg:
      arg_p = P.optional(parsers.char(' =')) >> leaves.option_argument
      return (name_p + arg_p).parsecmap(lambda n: Option(*n, self.definition))
    else:
      return name_p.parsecmap(lambda n: Option(n, None, self.definition))


long_illegal = parsers.non_symbol_chars | parsers.char('=')

usage_long_option = (
  P.unit(
    parsers.string('--') + base.ident(long_illegal)
  ).parsecmap(helpers.join_string).mark() + P.optional(parsers.char('=') >> leaves.option_argument)
).desc('long option (--long)').parsecmap(lambda n: Option(*n))

short_illegal = parsers.non_symbol_chars

usage_short_option = (
  (P.unit(parsers.char('-') + parsers.char(illegal=short_illegal))).parsecmap(helpers.join_string).mark()
).desc('short option (-a)').parsecmap(lambda n: Option(n, None, short_alias=n))

# Usage parser without the leading "-" to allow parsing "-abc" style option specs
# Prefix the parse result with a "-" in order to forward the proper identifier to Short()
usage_shortlist_option = (
  parsers.char(illegal=short_illegal)
).parsecmap(lambda n: '-' + n[0]).mark().desc('short option (-a)').parsecmap(lambda n: Option(n, None, short_alias=n))


def option(options: T.List[Option]):
  @P.generate('option')
  def p() -> helpers.GeneratorParser[groups.Sequence]:
    start = yield parsers.location
    opt = yield reduce(
      lambda mem, p: p | mem,
      [o.atom_parser for o in options],
      usage_long_option | usage_short_option
    )
    options.append(opt)
    opts = [opt]
    # multiple short options can be specified like "-abc".
    # Keep parsing if the previously parsed option does not have an argument
    while not opt.arg:
      # Recalculate this parser, the definitions change every iteration
      opt = (yield P.optional(reduce(
        lambda mem, p: p | mem if p else mem,
        [o.atom_parser_shortlist for o in options],
        usage_shortlist_option
      )))
      if opt is None:
        break
      opts.append(opt)
      if opt not in options:
        options.append(opt)
    end = yield parsers.location
    return groups.Sequence((start, opts, end))
  return p
