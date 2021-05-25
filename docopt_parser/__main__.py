#!/usr/bin/env python3
import sys
import os
import docopt
import logging
import termcolor
from docopt_parser import DocoptParseError, parse_strict, parse_partial, \
  __doc__ as pkg_doc, __name__ as root_name, __version__

log = logging.getLogger(root_name)

__doc__ = pkg_doc + """
Usage:
  docopt-parser [-S] ast
  docopt-parser -h
  docopt-parser --version

Options:
  -S         Disable strict parsing and show the partial AST
  --help -h  Show this help screen
  --version  Show the docopt.sh version
"""


def docopt_parser(params):
  try:
    doc = sys.stdin.read()
    if params['-S']:
      ast, parsed_doc = parse_partial(doc)
      if params['ast']:
        sys.stdout.write(repr(ast) + '\n')
      if parsed_doc != doc:
        ast = parse_strict(doc)
    else:
      ast = parse_strict(doc)
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
