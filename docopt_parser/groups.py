import typing as T
import parsec as P
from docopt_parser import base, leaves, parsers, helpers

class Choice(base.AstGroup):
  pass

class Sequence(base.AstGroup):
  pass

class Group(base.AstGroup):
  pass

class Optional(base.AstGroup):
  pass

class Repeatable(base.AstGroup):
  pass


# We don't use sepBy and sepEndBy in sequence and expr because their termination
# works by relying on the parser failing. This would result in those parsers
# not being able to fail meaningfully and the error simply happening further upstream

@P.generate('sequence')
def sequence() -> helpers.GeneratorParser[Sequence]:
  nodes: T.List[base.AstNode] = []
  start = yield parsers.location
  while (yield P.lookahead(P.optional((parsers.either | parsers.nl | P.eof()).result(True)))) is None:
    node, repeat = yield (atom + P.optional(P.unit(parsers.whitespaces >> parsers.ellipsis.mark())))
    if repeat is not None:
      node = Repeatable((repeat[0], [node], repeat[2]))
    nodes.append(node)
    if (yield P.optional(parsers.whitespaces1)) is None:
      break
  end = yield parsers.location
  return Sequence(((start, nodes, end)))

@P.generate('expression')
def expr() -> helpers.GeneratorParser[Choice]:
  start = yield parsers.location
  nodes: T.List[base.AstNode] = [(yield sequence)]
  while (yield P.optional((parsers.either << parsers.whitespaces))) is not None:
    nodes.append((yield sequence))
  end = yield parsers.location
  return Choice(((start, nodes, end)))

group = (
  parsers.char('(') >> expr.parsecmap(lambda n: [n]) << parsers.char(')')
).mark().desc('group').parsecmap(lambda n: Group(n))
optional = (
  parsers.char('[') >> expr.parsecmap(lambda n: [n]) << parsers.char(']')
).mark().desc('optional').parsecmap(lambda n: Optional(n))

# @P.generate('sequence')
# def option_list() -> helpers.GeneratorParser[Sequence]:
#   leaves.inline_long_option_spec.parsecmap(lambda n: [n])
#   | (
#     leaves.inline_short_option_spec + P.many(leaves.inline_shortlist_short_option_spec)
#   ).parsecmap(lambda n: [n[0]] + n[1])
# ).mark().parsecmap(lambda n: Sequence(n))

@P.generate('option list (-abc)')
def option_list() -> helpers.GeneratorParser[Sequence]:
  start = yield parsers.location
  opts = [(yield leaves.usage_short_option)]
  while (yield P.lookahead(P.optional(parsers.char(illegal=leaves.short_illegal)))) is not None:
    opts.append((yield leaves.usage_shortlist_option))
  end = yield parsers.location
  return Sequence((start, opts, end))

atom = (
  group | optional
  | leaves.options_shortcut | leaves.arg_separator
  | leaves.usage_long_option | option_list
  | leaves.argument | leaves.command
).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')
