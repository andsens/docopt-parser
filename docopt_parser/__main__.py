#!/usr/bin/env python3
from docopt_parser.parser import DocoptAst
import sys
import os
import docopt
import logging
import termcolor
from docopt_parser import DocoptParseError, __doc__ as pkg_doc, __name__ as root_name, __version__
from parsec import ParseError
from docopt_parser.parser_utils import explain_error

log = logging.getLogger(root_name)

__doc__ = pkg_doc + """
Usage:
  docopt-parser ast
  docopt-parser -h
  docopt-parser --version

Options:
  --help -h  Show this help screen
  --version  Show the docopt.sh version
"""


def docopt_parser(params):
  try:
    doc = sys.stdin.read()
    ast = DocoptAst.parse(doc)
    if params['ast']:
      sys.stdout.write(repr(ast) + '\n')
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
