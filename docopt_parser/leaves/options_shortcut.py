from docopt_parser import base, marks, parsers

options_shortcut = parsers.string('options').mark()\
  .desc('options shortcut').parsecmap(lambda n: OptionsShortcut((n[0], n[2])))

class OptionsShortcut(base.AstLeaf):
  def __init__(self, mark: marks.RangeTuple):
    super().__init__((mark[0], 'options', mark[1]))
