from .optional import Optional
from . import string

options_shortcut = string('options').desc('options shortcut').parsecmap(lambda s: OptionsShortcut())

class OptionsShortcut(Optional):
  def __init__(self):
    self.options = []

  @property
  def items(self):
    return list(filter(lambda o: o.shortcut, self.options))

  def __repr__(self):
    return f'''<OptionsShortcut>{self.repeatable_suffix}
{self.indent(self.items)}'''

  def __iter__(self):
    yield 'type', 'optionsshortcut'
    yield 'repeatable', self.repeatable
    yield 'items', self.items

  @property
  def multiple(self):
    return all(map(lambda i: i.multuple, self.items))

  @multiple.setter
  def multiple(self, value):
    for item in self.items:
      item.multiple = value
