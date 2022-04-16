from functools import reduce
import typing as T
import parsec as P
from docopt_parser import base, elements, parsers, helpers
from docopt_parser.groups.group import Group
from docopt_parser.groups.sequence import Sequence
from docopt_parser.groups.choice import Choice
from docopt_parser.groups.optional import Optional


@P.generate('atom')
def atom() -> helpers.GeneratorParser[base.AstLeaf]:
  # This indirection is necessary to avoid a circular dependency between:
  # expr -> seq -> atom -> expr
  from docopt_parser.groups import parsers
  return (yield (
    parsers.group | parsers.optional
    | elements.options_shortcut | elements.arg_separator | parsers.option_list
    | elements.argument | elements.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)'))

sequence = P.exclude(  # type: ignore
  P.sepEndBy(  # type: ignore
    (atom + P.optional(P.unit(parsers.whitespaces >> elements.repeatable))),
    parsers.whitespaces1
  ),
  P.lookahead(parsers.either | parsers.nl | P.eof())
).parsecmap(
  # Convert [(atom, None), (atom, Repeatable)] to [atom, atom, Repeatable]
  lambda pairs: [e for e in reduce(
    lambda memo, pair: memo + list(pair), pairs, T.cast(T.List[base.AstLeaf | elements.Repeatable | None], [])
  ) if e is not None]
).parsecmap(lambda n: Sequence(n))
expr = P.sepBy(  # type: ignore
  sequence,
  parsers.either << parsers.whitespaces
).parsecmap(lambda n: Choice(n))
group = (parsers.char('(') >> expr << parsers.char(')')).desc('group').parsecmap(lambda n: Group([n]))
optional = (parsers.char('[') >> expr << parsers.char(']')).desc('optional').parsecmap(lambda n: Optional([n]))
option_list = (
  elements.inline_long_option_spec
  | (
    elements.inline_short_option_spec + P.many(elements.inline_shortlist_short_option_spec)
  ).parsecmap(lambda n: Sequence([n[0]] + n[1]))
)
