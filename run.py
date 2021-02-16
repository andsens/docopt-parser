#!/usr/bin/env python3

# from tests.conftest import parse_usecases
# next(parse_usecases("tests/docopt-parser-usecases.txt"))


doc = '''Naval Fate.
Usage:
  prog ship new <name>...  | ship [<name>] move <x> <y> [--speed=<kn>]
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
# from docopt_parser.docopt import parse_section, formal_usage, docopt
# print(docopt(doc))
# print(formal_usage(parse_section('usage:', doc)[0]))
from docopt_parser.parsec import ParseError
from docopt_parser.parser import explain_error, option_line, long, parse, docopt_lang
# text = '--speed=<kn>  Speed in knots'
text = doc
try:
  # print(option_line.parse_strict(text))
  print(docopt_lang.parse(doc))
  print(docopt_lang.parse_strict(doc))
except ParseError as e:
  print(explain_error(e, text))
