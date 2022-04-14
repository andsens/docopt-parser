from typing import overload

from docopt_parser import elements, base, marked

class DocumentedOption(base.IdentNode):
  multiple = False
  short: elements.Short | None
  long: elements.Long | None
  shortcut: bool
  expects_arg: bool
  __default: marked.Marked[str] | None
  __doc: marked.Marked[str] | None
  mark: marked.Mark

  @overload
  def __init__(self,
               short: elements.Short, long: elements.Long | None, shortcut: bool,
               default: marked.MarkedTuple[str] | None, doc: marked.MarkedTuple[str] | None):
    pass

  @overload
  def __init__(self,
               short: elements.Short | None, long: elements.Long, shortcut: bool,
               default: marked.MarkedTuple[str] | None, doc: marked.MarkedTuple[str] | None):
    pass

  def __init__(self,
               short: elements.Short | None, long: elements.Long | None, shortcut: bool,
               default: marked.MarkedTuple[str] | None, doc: marked.MarkedTuple[str] | None):
    if long:
      super().__init__(long.ident)
    elif short:
      super().__init__(short.ident)
    self.short = short
    self.long = long
    self.shortcut = shortcut
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.__default = marked.Marked(default) if default else None
    self.__doc = marked.Marked(doc) if doc else None
    elements = [getattr(self.short, 'mark', None), getattr(self.long, 'mark', None), self.__default, self.__doc]
    self.mark = marked.Mark(
      min([e.start for e in elements if e is not None]), max([e.end for e in elements if e is not None])
    )

  @property
  def default(self):
    return self.__default.elm if self.__default else None

  @property
  def doc(self):
    return self.__doc.elm if self.__doc else None

  def __repr__(self):
    return f'''<Option{self.multiple_suffix}>{self.repeatable_suffix}
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  shortcut: {self.shortcut}
  arg?:     {self.expects_arg}
  default:  {self.default}
  doc:      {self.doc}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'short', dict(self.short) if self.short else None
    yield 'long', dict(self.long) if self.long else None
    yield 'shortcut', self.shortcut
    yield 'expects_arg', self.expects_arg
    yield 'default', self.default
    yield 'doc', self.doc
