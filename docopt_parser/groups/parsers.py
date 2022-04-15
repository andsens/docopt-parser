from typing import List, Tuple, cast
from parsec import eof, exclude, generate, lookahead, many, sepBy, sepEndBy, unit, optional as _optional  # type: ignore
from docopt_parser import base, elements, parsers, helpers
from docopt_parser.groups.sequence import Sequence
from docopt_parser.groups.choice import Choice
from docopt_parser.groups.optional import Optional


@generate('atom')
def atom() -> helpers.GeneratorParser[base.AstLeaf]:
  # This indirection is necessary to avoid a circular dependency between:
  # expr -> seq -> atom -> expr
  from docopt_parser.groups import parsers
  return (yield (
    parsers.group | parsers.optional
    | elements.options_shortcut | elements.arg_separator | parsers.option_list
    | elements.argument | elements.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)'))

def set_repeatable(elms: Tuple[base.AstLeaf, str | None]):
  if elms[1] is not None:
    elms[0].repeatable = True
  return elms[0]

sequence = exclude(
  sepEndBy(
    (atom + _optional(unit(parsers.whitespaces >> parsers.ellipsis)))
    .parsecmap(set_repeatable),
    parsers.whitespaces1
  ),
  lookahead(parsers.either | parsers.nl | eof())
).parsecmap(lambda n: Sequence(n))
expr = sepBy(sequence, parsers.either << parsers.whitespaces).parsecmap(lambda n: Choice(n))
group = (parsers.char('(') >> expr << parsers.char(')')).desc('group')
optional = (parsers.char('[') >> expr << parsers.char(']')) \
  .desc('optional').parsecmap(lambda n: Optional([n] if n is not None else []))
option_list = (
  elements.inline_long_option_spec
  | (
    elements.inline_short_option_spec + many(elements.inline_shortlist_short_option_spec)
  ).parsecmap(lambda n: Sequence(cast(List[base.AstLeaf], [n[0]] + n[1])))
)
