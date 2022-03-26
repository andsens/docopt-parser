from typing import Iterator, Union
from .option import Option
from .long import Long
from .short import Short
from .identnode import IdentNode

class OptionRef(IdentNode):
  Union[Short, Long]
  ref: Option
  arg: str

  def __init__(self, option: Union[Short, Long], ref: Option, arg: str):
    super().__init__(option.ident)
    self.option = option
    self.ref = ref
    self.arg = arg

  def __repr__(self) -> str:
    return f'''<OptionRef>{self.repeatable_suffix}
  {self.indent(self.ref)}
  refarg: {self.arg}'''

  def __iter__(self) -> Iterator[tuple[str, Union[str, bool, Option]]]:
    yield 'type', 'optionref'
    yield 'repeatable', self.repeatable
    yield 'arg', self.arg
    yield 'ref', self.ref

  @property
  def multiple(self) -> bool:
    return self.option.multiple

  @multiple.setter
  def multiple(self, value: bool) -> None:
    self.option.multiple = value
