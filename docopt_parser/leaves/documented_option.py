import typing as T
import parsec as P
import re

from docopt_parser import leaves, base, marks, helpers, parsers


class DocumentedOption(base.IdentNode):
  multiple = False
  short: leaves.Short | None
  long: leaves.Long | None
  shortcut: bool
  expects_arg: bool
  __default: marks.Marked[str] | None
  __doc: marks.Marked[str] | None

  @T.overload
  def __init__(self, range: marks.RangeTuple,
               short: leaves.Short, long: leaves.Long | None,
               default: marks.MarkedTuple[str] | None, doc: marks.MarkedTuple[str] | None):
    pass

  @T.overload
  def __init__(self, range: marks.RangeTuple,
               short: leaves.Short | None, long: leaves.Long,
               default: marks.MarkedTuple[str] | None, doc: marks.MarkedTuple[str] | None):
    pass

  def __init__(self, range: marks.RangeTuple,
               short: leaves.Short | None, long: leaves.Long | None,
               default: marks.MarkedTuple[str] | None, doc: marks.MarkedTuple[str] | None):
    if long:
      super().__init__((range[0], long.ident, range[1]))
    elif short:
      super().__init__((range[0], short.ident, range[1]))
    self.short = short
    self.long = long
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.__default = marks.Marked(default) if default else None
    self.__doc = marks.Marked(doc) if doc else None

  @property
  def default(self):
    return self.__default.elm if self.__default else None

  @property
  def doc(self):
    return self.__doc.elm if self.__doc else None

  def __repr__(self):
    return f'''<DocumentedOption>
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  arg?:     {self.expects_arg}
  default:  {self.default}
  doc:      {self.doc}'''

  def __iter__(self):
    yield from super().__iter__()
    yield 'short', dict(self.short) if self.short else None
    yield 'long', dict(self.long) if self.long else None
    yield 'expects_arg', self.expects_arg
    yield 'default', self.default
    yield 'doc', self.doc


next_documented_option = parsers.nl + P.optional(parsers.indent) + parsers.char('-')
terminator = (parsers.nl + parsers.nl) ^ (parsers.nl + P.eof()) ^ next_documented_option
default = (
  P.regex(r'\[default: ', re.IGNORECASE) >> P.many(parsers.char(illegal='\n]')) << parsers.char(']')  # type: ignore
).desc('[default: ]').parsecmap(helpers.join_string)
doc = P.many1(parsers.char(illegal=default ^ terminator)).desc('option documentation').parsecmap(helpers.join_string)

@P.generate('short option (-s)')
def option_line_short() -> helpers.GeneratorParser[leaves.Short]:
  argspec = (parsers.char(' =') >> leaves.argument).desc('argument')
  name = yield (parsers.char('-') + parsers.char(illegal=leaves.short_illegal)).parsecmap(helpers.join_string).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return leaves.Short(name, arg)

@P.generate('long option (--long)')
def option_line_long() -> helpers.GeneratorParser[leaves.Long]:
  argspec = (parsers.char(' =') >> leaves.argument).desc('argument')
  name = yield (parsers.string('--') + base.ident(leaves.long_illegal)).parsecmap(helpers.join_string).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return leaves.Long(name, arg)

@P.generate('options')
def option_line_opts() -> helpers.GeneratorParser[
  T.Tuple[leaves.Short, leaves.Long]
  | T.Tuple[leaves.Short, None]
  | T.Tuple[None, leaves.Long]
]:
  first = yield option_line_long | option_line_short
  if isinstance(first, leaves.Long):
    opt_short = yield P.optional((parsers.string(', ') | parsers.char(' ')) >> option_line_short)
    opt_long = first
  else:
    opt_short = first
    opt_long = yield P.optional((parsers.string(', ') | parsers.char(' ')) >> option_line_long)
  if opt_short is not None and opt_long is not None:
    if opt_short.arg is not None and opt_long.arg is None:
      opt_long.arg = opt_short.arg
    if opt_short.arg is None and opt_long.arg is not None:
      opt_short.arg = opt_long.arg
  return (opt_short, opt_long)

@P.generate('documented option')
def documented_option() -> helpers.GeneratorParser[DocumentedOption]:
  _doc = _default = None
  start: marks.LocInfo = yield parsers.location
  (short, long) = yield option_line_opts
  if (yield P.optional(P.lookahead(parsers.eol))) is not None:
    # Consume trailing whitespaces
    yield parsers.whitespaces
  elif (yield P.optional(P.lookahead(parsers.char(illegal='\n')))) is not None:
    yield (parsers.char(' ') + P.many1(parsers.char(' '))) ^ P.fail_with('at least 2 spaces')  # type: ignore
    _default = yield P.lookahead(P.optional(doc) >> P.optional(default).mark() << P.optional(doc))
    _doc = yield P.optional(doc).mark()
  end = yield parsers.location
  return DocumentedOption((start, end), short, long, _default, _doc)
