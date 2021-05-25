from parsec import generate
from ..option import SpecSource
from .. import string

def options_shortcut(options):
  @generate('options shortcut')
  def p():
    yield string('options')
    return list(filter(lambda o: o.source == SpecSource.OPTIONS, options))
  return p
