#!/usr/bin/env python3
from parsec import ParseError
from docopt_parser.parser import ast_tostr, explain_error, docopt_lang

doc = '''Naval Fate.
Usage:
  prog ship new <name>...  | ship [<name>] move <x> <y> [--speed=<kn>]
  prog ship shoot <x> <y>
  prog mine (set|remove) <x> <y> [--moored|--drifting]
  prog -h | --help
  prog --version
  prog [-hv]

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Mored (anchored) mine.
  --drifting    Drifting mine.
'''

try:
  print(ast_tostr(docopt_lang.parse_strict(doc)))
except ParseError as e:
  print(explain_error(e, doc))
