#!/usr/bin/env python3
import typing as T
import sys
import os
import docopt
import logging
import termcolor
import yaml

# pyright: reportUnknownVariableType=false
from docopt_parser import DocoptError, parse, __doc__ as pkg_doc, \
  __name__ as root_name, __version__
# , merge_identical_leaves

log = logging.getLogger(root_name)

__doc__: str = T.cast(str, pkg_doc) + """
Usage:
  docopt-parser [-y] ast
  docopt-parser -h
  docopt-parser --version

Options:
  -y --yaml  Output the AST in YAML format
  --help -h  Show this help screen
  --version  Show the docopt.sh version
"""
Params = T.TypedDict('Params', {'--yaml': bool, 'ast': bool})

def docopt_parser(params: Params):
  try:
    text = sys.stdin.read()
    ast = parse(text)
    if params['ast']:
      # ast = merge_identical_leaves(ast)
      sys.stdout.write(yaml.dump(ast.dict, sort_keys=False) if params['--yaml'] else repr(ast) + '\n')
  except DocoptError as e:
    log.error(str(e))
    sys.exit(e.exit_code)


def setup_logging():
  level_colors = {
    logging.ERROR: 'red',
    logging.WARN: 'yellow',
  }

  class ColorFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord):
        record.msg = termcolor.colored(str(record.msg), level_colors.get(record.levelno, None))
        return super(ColorFormatter, self).format(record)

  stderr = logging.StreamHandler(sys.stderr)
  if os.isatty(2):
    stderr.setFormatter(ColorFormatter())
  log.setLevel(level=logging.INFO)
  log.addHandler(stderr)


def main():
  setup_logging()
  params = T.cast(Params, docopt.docopt(__doc__, version=__version__))
  docopt_parser(params)


if __name__ == '__main__':
  main()
