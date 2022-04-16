from docopt_parser import base, marks, parsers

options_shortcut = parsers.string('options').mark().desc('options shortcut').parsecmap(lambda n: OptionsShortcut(n))

class OptionsShortcut(base.AstLeaf):
  def __init__(self, text: marks.MarkedTuple[str]):
    super().__init__((text[0], text[2]))
