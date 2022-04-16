import parsec as P

from docopt_parser import base, parsers

arg_separator = P.unit(parsers.string('--') << P.lookahead(parsers.non_symbol_chars)).mark() \
  .parsecmap(lambda n: ArgumentSeparator((n[0], n[2])))

class ArgumentSeparator(base.AstLeaf):
  pass
