from .. import char
from .choice import expr

def group(options):
  return (char('(') >> expr(options) << char(')'))
