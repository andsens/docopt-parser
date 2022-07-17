import typing as T
import parsec as P
import re

from docopt_parser import leaves, base
from docopt_parser.util import errors, helpers, marks, parsers


@P.generate('short option (-s)')
def option_line_short() -> helpers.GeneratorParser[T.Tuple[marks.MarkedTuple[str], "marks.MarkedTuple[str] | None"]]:
  argspec = (parsers.char(' =') >> documented_option_argument).desc('argument')
  name = yield (parsers.char('-') + parsers.char(illegal=leaves.short_illegal)).parsecmap(helpers.join_string).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return (name, arg)

@P.generate('long option (--long)')
def option_line_long() -> helpers.GeneratorParser[T.Tuple[marks.MarkedTuple[str], "marks.MarkedTuple[str] | None"]]:
  argspec = (parsers.char(' =') >> documented_option_argument).desc('argument')
  name = yield (
    parsers.string('--') + base.ident(leaves.long_illegal | parsers.char(','))
  ).parsecmap(helpers.join_string).mark()
  if (yield P.optional(P.lookahead(parsers.char('=')))) is not None:
    # Definitely an argument, make sure we fail with "argument expected"
    arg = yield argspec
  else:
    arg = yield P.optional(argspec)
  return (name, arg)

next_documented_option = parsers.nl + parsers.indent + parsers.char('-')
terminator = (parsers.nl + parsers.nl) ^ (parsers.nl + P.eof()) ^ next_documented_option
default = (
  P.regex(r'\[default: ', re.IGNORECASE) + P.many(parsers.char(illegal='\n]')) + parsers.char(']')  # type: ignore
).desc('[default: ]')
default_value = default.parsecmap(lambda n: n[0][1]).parsecmap(helpers.join_string).mark()
option_documentation = P.many1(
  parsers.char(illegal=default ^ terminator)
).desc('option documentation').parsecmap(helpers.join_string)
documented_option_argument = (
  leaves.wrapped_arg ^ base.ident(parsers.char(' ,'), starts_with=parsers.char(illegal=parsers.char(' ,-'))).mark()
).desc('argument')


def get_option_definition(name: str, options: T.List[leaves.Option]) -> "leaves.Option | None":
  for o in options:
    if o.ident == name:
      return o.definition

def documented_option(options: T.List[leaves.Option]):
  @P.generate('documented option')
  def p() -> helpers.GeneratorParser[None]:
    short_alias: "marks.MarkedTuple[str] | None" = None
    opts: T.List[T.Tuple[marks.MarkedTuple[str], "marks.MarkedTuple[str] | None"]] = []
    opt_def: "T.Tuple[marks.MarkedTuple[str], marks.MarkedTuple[str] | None] | None" = None
    while True:
      opt = yield option_line_long | option_line_short
      if opt[0][1].startswith('--'):
        # The last long option is the definition
        opt_def = opt
      else:
        if opt_def is None:
          # In the absence of long options, the short option is the definition
          opt_def = opt
        if short_alias is not None:
          raise errors.DocoptParseError(
            f'An option may only have one short option alias (previously defined at {short_alias})',
            marks.Marked(opt[0]))
        short_alias = opt[0]
      opts.append(opt)
      next_opt = yield P.unit(
        P.optional((parsers.string(', ') | parsers.char(' ')) >> P.lookahead(parsers.char('-')))
      )
      if next_opt is None:
        break
    opt_def = T.cast(T.Tuple[marks.MarkedTuple[str], "marks.MarkedTuple[str] | None"], opt_def)
    opts.remove(opt_def)

    _doc: "marks.MarkedTuple[str] | None" = None
    _default: "marks.MarkedTuple[str] | None" = None
    if (yield P.optional(P.lookahead(parsers.eol))) is not None:
      # Consume trailing whitespaces
      yield parsers.whitespaces
    elif (yield P.optional(P.lookahead(parsers.char(illegal='\n')))) is not None:
      yield (parsers.char(' ') + P.many1(parsers.char(' '))) ^ P.fail_with('at least 2 spaces')  # type: ignore
      _default = yield P.lookahead(P.optional(option_documentation) >> P.optional(default_value))
      _doc = yield P.optional(
        P.optional(option_documentation) + P.optional(default) + P.optional(option_documentation)
      ).parsecmap(helpers.join_string).mark()

    def_arg = opt_def[1]
    if def_arg is None:
      def_arg = next((o[1] for o in opts if o[1] is not None), None)
    definition = leaves.Option(opt_def[0], def_arg, None, short_alias, _default, _doc)
    previous_def = get_option_definition(definition.ident, options)
    if previous_def and previous_def.ident == definition.ident:
      raise errors.DocoptParseError(
        f'{definition.ident} has already been specified at {previous_def.mark.start}', definition.mark)
    options.append(definition)

    for name, arg in opts:
      opt = leaves.Option(name, arg, definition)
      previous_def = get_option_definition(opt.ident, options)
      if previous_def and previous_def.ident == opt.ident:
        raise errors.DocoptParseError(
          f'{definition.ident} has already been specified at {previous_def.mark.start}', definition.mark)
      options.append(opt)
  return p


@P.generate('option sections')
def documented_options() -> helpers.GeneratorParser[T.List[leaves.Option]]:
  section_title = P.regex(r'[^\n]*options:', re.I)  # type: ignore
  non_option_section_text = P.optional(parsers.text(section_title))
  options: T.List[leaves.Option] = []
  while (yield P.optional(P.eof().result(True))) is None:
    if (yield P.optional(non_option_section_text)) is not None:
      # skip anything non-option related
      continue
    yield section_title
    yield parsers.whitespaces >> P.optional(parsers.nl + parsers.indent)
    while (yield P.lookahead(P.optional(parsers.char('-')))) is not None:
      yield documented_option(options)
      if (yield P.lookahead(P.optional(next_documented_option))) is None:
        break
      yield parsers.nl + P.optional(parsers.indent)
    yield P.eof() | parsers.nl
  return options
