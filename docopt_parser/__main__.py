#!/usr/bin/env python3
import sys
import os
import docopt
import logging
import json
import termcolor
from . import DocoptParseError, __doc__ as pkg_doc, __name__ as root_name, __version__
from .parser import parse_doc

log = logging.getLogger(root_name)

__doc__ = pkg_doc + """
Usage:
  docopt-parser [options]

Options:
  --help -h            Show this help screen
  --version            Show the docopt.sh version
"""


def docopt_parser(params):
  try:
    ast = parse_doc(sys.stdin.read())
    sys.stdout.write("%s\n" % json.dumps(ast, indent=2))
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
