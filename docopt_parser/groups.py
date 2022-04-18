import typing as T
import parsec as P

from docopt_parser import base, leaves
from docopt_parser.util import helpers, parsers

class Choice(base.Group):
  pass

class Sequence(base.Group):
  pass

class Group(base.Group):
  pass

class Optional(base.Group):
  pass

class Repeatable(base.Group):
  pass


def atom(options: T.List[leaves.Option]):
  return (
    group(options) | optional(options)
    | leaves.options_shortcut | leaves.arg_separator
    | leaves.option(options)
    | leaves.argument | leaves.command
  ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')

# We don't use sepBy and sepEndBy in sequence and expr because their termination
# works by relying on the parser failing. This would result in those parsers
# not being able to fail meaningfully and the error simply happening further upstream

def sequence(options: T.List[leaves.Option]):
  @P.generate('sequence')
  def p() -> helpers.GeneratorParser[Sequence]:
    nodes: T.List[base.Node] = []
    start = yield parsers.location
    while (yield P.lookahead(P.optional((parsers.either | parsers.nl | P.eof()).result(True)))) is None:
      node, repeat = yield (atom(options) + P.optional(P.unit(parsers.whitespaces >> parsers.ellipsis.mark())))
      if repeat is not None:
        node = Repeatable((repeat[0], [node], repeat[2]))
      nodes.append(node)
      if (yield P.optional(parsers.whitespaces1)) is None:
        break
    end = yield parsers.location
    return Sequence(((start, nodes, end)))
  return p

def expr(options: T.List[leaves.Option]):
  @P.generate('expression')
  def p() -> helpers.GeneratorParser[Choice]:
    start = yield parsers.location
    nodes: T.List[base.Node] = [(yield sequence(options))]
    while (yield P.optional((parsers.either << parsers.whitespaces))) is not None:
      nodes.append((yield sequence(options)))
    end = yield parsers.location
    return Choice(((start, nodes, end)))
  return p

def group(options: T.List[leaves.Option]):
  return (
    parsers.char('(') >> expr(options).parsecmap(lambda n: [n]) << parsers.char(')')
  ).mark().desc('group').parsecmap(lambda n: Group(n))

def optional(options: T.List[leaves.Option]):
  return (
    parsers.char('[') >> expr(options).parsecmap(lambda n: [n]) << parsers.char(']')
  ).mark().desc('optional').parsecmap(lambda n: Optional(n))
