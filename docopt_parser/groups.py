from functools import reduce
import typing as T
import parsec as P
from docopt_parser import base, leaves, parsers, helpers

class Choice(base.AstGroup):
  pass

class Group(base.AstGroup):
  pass

class Optional(base.AstGroup):
  pass

class Sequence(base.AstGroup):
  pass

@P.generate('atom')
def atom() -> helpers.GeneratorParser[base.AstNode]:
  # This indirection is necessary to avoid a circular dependency between:
  # expr -> seq -> atom -> expr
  from docopt_parser import groups
  return (yield (
    groups.group | groups.optional
    | leaves.options_shortcut | leaves.arg_separator | groups.option_list
    | leaves.argument | leaves.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)'))

sequence = P.exclude(  # type: ignore
  P.sepEndBy(  # type: ignore
    (atom + P.optional(P.unit(parsers.whitespaces >> leaves.repeatable))),
    parsers.whitespaces1
  ),
  P.lookahead(parsers.either | parsers.nl | P.eof())
).parsecmap(
  # Convert [(atom, None), (atom, Repeatable)] to [atom, atom, Repeatable]
  lambda pairs: [e for e in reduce(
    lambda memo, pair: memo + list(pair), pairs, T.cast(T.List[base.AstNode | leaves.Repeatable | None], [])
  ) if e is not None]
).mark().parsecmap(lambda n: Sequence(n))
expr = P.sepBy(  # type: ignore
  sequence,
  parsers.either << parsers.whitespaces
).mark().parsecmap(lambda n: Choice(n))
group = (
  parsers.char('(') >> expr.parsecmap(lambda n: [n]) << parsers.char(')')
).mark().desc('group').parsecmap(lambda n: Group(n))
optional = (
  parsers.char('[') >> expr.parsecmap(lambda n: [n]) << parsers.char(']')
).mark().desc('optional').parsecmap(lambda n: Optional(n))
option_list = (
  (
    leaves.inline_long_option_spec.parsecmap(lambda n: [n])
    | (
      leaves.inline_short_option_spec + P.many(leaves.inline_shortlist_short_option_spec)
    ).parsecmap(lambda n: [n[0]] + n[1])
  ).mark().parsecmap(lambda n: Sequence(n))
)
