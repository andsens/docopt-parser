from .. import char
from .choice import expr

class Group(object):
  def group(options):
    return (char('(') >> expr(options) << char(')'))
