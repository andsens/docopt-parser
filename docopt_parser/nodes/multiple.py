from .astnode import AstNode

class Multiple(AstNode):
  def __init__(self, item):
    self.item = item

  def __repr__(self):
    return f'''<Multiple>: {self.item}'''
