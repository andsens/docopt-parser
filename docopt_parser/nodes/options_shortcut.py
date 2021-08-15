from parsec import generate
from .optional import Optional
from . import string

def options_shortcut(options):
  @generate('options shortcut')
  def p():
    yield string('options')
    return OptionsShortcut(options)
  return p

class OptionsShortcut(Optional):
  def __init__(self, options):
    self.options = options

  @property
  def items(self):
    return list(filter(lambda o: o.shortcut, self.options))

  def __repr__(self):
    return f'''<OptionsShortcut>{self.repeatable_suffix}
{self.indent(self.items)}'''
