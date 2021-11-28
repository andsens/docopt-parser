from .identnode import IdentNode

class Option(IdentNode):
  multiple = False

  def __init__(self, short, long, shortcut, doc1, default, doc2):
    super().__init__(long.ident if long else short.ident)
    self.short = short
    self.long = long
    self.shortcut = shortcut
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.default = default
    self.doc = ''.join(t for t in [
      doc1 or '',
      default or f'[default: {default}]',
      doc2 or '',
    ])

  def __repr__(self):
    return f'''<Option{self.multiple_suffix}>{self.repeatable_suffix}
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  shortcut: {self.shortcut}
  arg?:     {self.expects_arg}
  default:  {self.default}
  doc:      {self.doc}'''

  def __iter__(self):
    yield 'short', dict(self.short) if self.short else None
    yield 'long', dict(self.long) if self.long else None
    yield 'shortcut', self.shortcut
    yield 'expects_arg', self.expects_arg
    yield 'default', self.default
    yield 'doc', self.doc
