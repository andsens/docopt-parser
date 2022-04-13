from typing import Iterator, Union
from .long import Long
from .short import Short
from .identnode import IdentNode
from ..marked import Mark, Marked, MarkedTuple

class Option(IdentNode):
  multiple = False
  short: Union[Short, None]
  long: Union[Long, None]
  shortcut: bool
  expects_arg: bool
  __default: Union[Marked, None]
  __doc: Union[Marked, None]
  mark: Mark

  def __init__(self,
               short: Union[Short, None], long: Union[Long, None], shortcut: bool,
               default: Union[MarkedTuple, None], doc: Union[MarkedTuple, None]):
    super().__init__(long.ident if long else short.ident)
    self.short = short
    self.long = long
    self.shortcut = shortcut
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.__default = Marked(default) if default else None
    self.__doc = Marked(doc) if doc else None
    elements = [getattr(self.short, 'mark', None), getattr(self.long, 'mark', None), self.__default, self.__doc]
    self.mark = Mark(min([e.start for e in elements if e is not None]), max([e.end for e in elements if e is not None]))

  @property
  def default(self) -> Union[str, None]:
    return self.__default.txt if self.__default else None

  @property
  def doc(self) -> Union[str, None]:
    return self.__doc.txt if self.__doc else None

  def __repr__(self) -> str:
    return f'''<Option{self.multiple_suffix}>{self.repeatable_suffix}
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  shortcut: {self.shortcut}
  arg?:     {self.expects_arg}
  default:  {self.default}
  doc:      {self.doc}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, None]]]:
    yield 'short', dict(self.short) if self.short else None
    yield 'long', dict(self.long) if self.long else None
    yield 'shortcut', self.shortcut
    yield 'expects_arg', self.expects_arg
    yield 'default', self.default
    yield 'doc', self.doc
