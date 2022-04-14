from functools import total_ordering
from typing import Any, Callable, Generic, Tuple, TypeVar
from parsec import ParseError

T = TypeVar('T')
LocInfo = Tuple[int, int]
MarkedTuple = Tuple[LocInfo, T, LocInfo]

def is_marked_tuple(marked_tuple: Any) -> bool:
  if not isinstance(marked_tuple, tuple):
    return False
  if len(marked_tuple) != 3:  # type: ignore
    return False
  if not is_loc_info(marked_tuple[0]):
    return False
  if not is_loc_info(marked_tuple[2]):
    return False
  return True

def is_loc_info(loc_info: Any) -> bool:
  if not isinstance(loc_info, tuple):
    return False
  if len(loc_info) != 2:  # type: ignore
    return False
  if not isinstance(loc_info[0], int):
    return False
  if not isinstance(loc_info[1], int):
    return False
  return True

U = TypeVar('U')
def unwrappedMarked(function: Callable[[T], U], marked: MarkedTuple[T]) -> MarkedTuple[U]:
  start, elm, end = marked
  return (start, function(elm), end)

@total_ordering
class Location(object):
  line: int
  col: int

  def __init__(self, loc: LocInfo):
    super().__init__()
    self.line, self.col = loc

  def __eq__(self, other: object):
    return isinstance(other, Location) and self.line == other.line and self.col == other.col

  def __lt__(self, other: object):
    if not isinstance(other, Location):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.line < other.line or (self.line == other.line and self.col < other.col)

  def show(self, text: str):
    lines = text.split('\n')
    prev_line = ''
    if self.line > 0:
      prev_line = lines[self.line - 1]
    col_offset = ' ' * self.col
    return f'\n{prev_line}\n{lines[self.line]}\n{col_offset}^'

@total_ordering
class Mark(object):
  start: Location
  end: Location

  def __init__(self, start: Location, end: Location):
    super().__init__()
    self.start = start
    self.end = end

  def __eq__(self, other: object):
    return isinstance(other, Mark) and self.start == other.start and self.end == other.end

  def __lt__(self, other: object):
    if not isinstance(other, Mark):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.start < other.start or (self.start == other.start and self.end < other.end)

  def show(self, text: str):
    lines = text.split('\n')
    if self.start.line == self.end.line:
      prev_line = ''
      if self.start.line > 0:
        prev_line = lines[self.start.line - 1] + '\n'
      line = lines[self.start.line]
      if line.strip() == line[self.start.col:self.end.col].strip():
        return f'{prev_line}{line} <---'
      else:
        start_col_offset = ' ' * self.start.col
        underline = '~' * (self.end.col - self.start.col)
        return f'{prev_line}{line}\n{start_col_offset}{underline}'
    else:
      all_lines = '\n'.join(lines[self.start.line:self.end.line])
      start_col_offset = ' ' * self.start.col
      end_col_offset = ' ' * self.end.col
      return f'{start_col_offset}V\n{all_lines}\n{end_col_offset}^'

class Marked(Mark, Generic[T]):
  elm: T

  def __init__(self, mark: MarkedTuple[T]):
    start, txt, end = mark
    super().__init__(Location(start), Location(end))
    self.elm = txt


def explain_error(e: ParseError, text: str) -> str:
  loc = Location(e.loc_info(e.text, e.index))
  return f'\n{loc.show(text)}^\n{str(e)}'
