#!/usr/bin/env python3

# from tests.conftest import parse_usecases
# next(parse_usecases("tests/docopt-parser-usecases.txt"))

from docopt_parser.parser import docopt
from docopt_parser.docopt import parse_section, formal_usage

doc = '''Naval Fate.
Usage:
  prog ship new <name>...
  prog ship [<name>] move <x> <y> [--speed=<kn>]
  prog ship shoot <x> <y>
  prog mine (set|remove) <x> <y> [--moored|--drifting]
  prog -h | --help
  prog --version
Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Mored (anchored) mine.
  --drifting    Drifting mine.

'''

print(docopt.parse(doc))
print(parse_section('usage:', doc))
