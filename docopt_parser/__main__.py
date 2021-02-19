#!/usr/bin/env python3
from docopt_parser.validate import validate
from docopt_parser.optimize import optimize
from docopt_parser.parser_utils import ast_tostr
import sys
import os
import docopt
import logging
import termcolor
from docopt_parser import DocoptParseError, __doc__ as pkg_doc, __name__ as root_name, __version__
from docopt_parser.parser import docopt_lang
from parsec import ParseError
from docopt_parser.parser_utils import explain_error

log = logging.getLogger(root_name)

__doc__ = pkg_doc + """
Usage:
  docopt-parser [-O] ast
  docopt-parser -h
  docopt-parser --version

Options:
  -O         Do not optimize the AST
  --help -h  Show this help screen
  --version  Show the docopt.sh version
"""


def docopt_parser(params):
  try:
    doc = sys.stdin.read()
    try:
      ast = docopt_lang.parse_strict(doc)
      validate(ast)
      if not params['-O']:
        ast = optimize(ast)
    except ParseError as e:
      raise DocoptParseError(explain_error(e, doc)) from None
    if params['ast']:
      txt_ast = ast_tostr(ast)
      sys.stdout.write(txt_ast)
  except DocoptParseError as e:
    log.error(str(e))
    sys.exit(e.exit_code)



def setup_logging():
  level_colors = {
    logging.ERROR: 'red',
    logging.WARN: 'yellow',
  }

  class ColorFormatter(logging.Formatter):

    def format(self, record):
        record.msg = termcolor.colored(str(record.msg), level_colors.get(record.levelno, None))
        return super(ColorFormatter, self).format(record)

  stderr = logging.StreamHandler(sys.stderr)
  if os.isatty(2):
    stderr.setFormatter(ColorFormatter())
  log.setLevel(level=logging.INFO)
  log.addHandler(stderr)


def main():
  setup_logging()
  params = docopt.docopt(__doc__, version=__version__)
  docopt_parser(params)


if __name__ == '__main__':
  main()
