from docopt_parser import base
from docopt_parser.util import parsers

class OptionsShortcut(base.Leaf):
  pass

options_shortcut = parsers.string('options').mark()\
  .desc('options shortcut').parsecmap(lambda n: OptionsShortcut(n))
