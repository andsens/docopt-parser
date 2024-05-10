#!/usr/bin/env python3
import logging
import os
import sys
import typing as T
import docopt
import termcolor
import yaml
import importlib.metadata

from docopt_parser import DocoptError, parse, __doc__ as pkg_doc, \
  __name__ as root_name
from docopt_parser.util.post_processors import collapse_groups, \
  merge_identical_groups, merge_identical_leaves

log = logging.getLogger(root_name)

__doc__: str = pkg_doc + """
Usage:
  docopt-parser [-y] ast
  docopt-parser -h
  docopt-parser --version

Options:
  -y --yaml  Output the AST in YAML format
  --help -h  Show this help screen
  --version  Show the docopt-parser version
"""
Params = T.TypedDict('Params', {'--yaml': bool, 'ast': bool})

def docopt_parser(params: Params):
  try:
    text = sys.stdin.read()
    ast = parse(text)
    ast = merge_identical_leaves(ast, ignore_option_args=True)
    ast = merge_identical_groups(ast)
    ast = collapse_groups(ast)
    if params['ast']:
      sys.stdout.write(
        yaml.dump(ast.dict, sort_keys=False) if params['--yaml'] else repr(ast) + '\n')
  except DocoptError as err:
    log.error(str(err))
    sys.exit(err.exit_code)


def setup_logging():
  level_colors = {
    logging.ERROR: 'red',
    logging.WARN: 'yellow',
  }

  class ColorFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord):
      record.msg = termcolor.colored(str(record.msg), level_colors.get(record.levelno, None))  # type: ignore
      return super().format(record)

  stderr = logging.StreamHandler(sys.stderr)
  if os.isatty(2):
    stderr.setFormatter(ColorFormatter())
  log.setLevel(level=logging.INFO)
  log.addHandler(stderr)


def main():
  setup_logging()
  try:
    version = 'v' + importlib.metadata.version('docopt-parser')
  except importlib.metadata.PackageNotFoundError:
    version = 'v0.0.0-dev'
  params = T.cast(Params, docopt.docopt(__doc__, version=version))
  docopt_parser(params)


if __name__ == '__main__':
  main()
