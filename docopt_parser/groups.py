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
  @P.generate('any element (cmd, ARG, options, --option, (group), [optional], --)')
  def p() -> helpers.GeneratorParser[T.List[base.Node]]:
    nodes = yield (
      group(options) | optional(options)
      | leaves.options_shortcut | leaves.arg_separator
      | leaves.option(options)
      | leaves.argument | leaves.command
    )
    if isinstance(nodes, base.Node):
      return [nodes]
    else:
      return nodes
  return p

# We don't use sepBy and sepEndBy in sequence and expr because their termination
# works by relying on the parser failing. This would result in those parsers
# not being able to fail meaningfully and the error simply happening further upstream

sequence_terminators = parsers.char('|)]\n\r\b\f\x1B\x07\0') | P.eof()

def sequence(options: T.List[leaves.Option]):
  @P.generate('sequence')
  def p() -> helpers.GeneratorParser[base.Node]:
    nodes: T.List[base.Node] = []
    start = yield parsers.location
    while (yield P.lookahead(P.optional(sequence_terminators.result(True)))) is None:
      atoms, repeat = yield (atom(options) + P.optional(P.unit(parsers.whitespaces >> parsers.ellipsis.mark())))
      if repeat is not None:
        # The node.mark.start is not a typo, we want it's start to span across the entire repeatable group
        atoms = [Repeatable((atoms[-1].mark.start.to_tuple(), atoms, repeat[2]))]
      nodes += atoms
      if (yield P.optional(parsers.whitespaces1)) is None:
        break
    end = yield parsers.location
    if len(nodes) == 1:
      return nodes[0]
    else:
      return Sequence(((start, nodes, end)))
  return p

def expr(options: T.List[leaves.Option]):
  @P.generate('expression')
  def p() -> helpers.GeneratorParser[base.Node]:
    start = yield parsers.location
    nodes: T.List[base.Group] = [(yield sequence(options))]
    while (yield P.optional((parsers.either << parsers.whitespaces))) is not None:
      nodes.append((yield sequence(options)))
    end = yield parsers.location
    if len(nodes) == 1:
      return nodes[0]
    else:
      return Choice(((start, nodes, end)))
  return p

def group(options: T.List[leaves.Option]):
  return (
    parsers.char('(') >> parsers.whitespaces >> expr(options).parsecmap(lambda n: [n]) << parsers.char(')')
  ).mark().desc('group').parsecmap(lambda n: Group(n))

def optional(options: T.List[leaves.Option]):
  return (
    parsers.char('[') >> parsers.whitespaces >> expr(options) << parsers.char(']')
  ).mark().desc('optional').parsecmap(
    # Strip the implicit <Sequence> if one exists, it is easier to parse this way but semantically incorrect
    lambda n: Optional((n[0], n[1].items if isinstance(n[1], Sequence) else [n[1]], n[2]))
  )
