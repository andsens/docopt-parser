from functools import total_ordering
from typing import Generic, Tuple, TypeVar
from parsec import ParseError

T = TypeVar('T')
LocInfo = Tuple[int, int]
MarkedTuple = Tuple[LocInfo, T, LocInfo]

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

  def __repr__(self):
    # All text editors use 1 indexed lines, show the location as such
    return f'{self.line + 1}:{self.col}'

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

  def __repr__(self):
    return f'{self.start}-{self.end}'

  def show(self, text: str):
    lines = text.split('\n')
    start = Location((self.start.line, self.start.col))
    end = Location((self.end.line, self.end.col))
    # If "end" is at column 0 on a new line,
    # move the location back to the end of the previous line.
    if end.col == 0 and end > start:
      end.line -= 1
      end.col = len(lines[end.line])
    if start.line == end.line:
      prev_line = ''
      if start.line > 0:
        prev_line = lines[start.line - 1] + '\n'
      line = lines[start.line]
      if line.strip() == line[start.col:end.col].strip():
        return f'{prev_line}{line} <---'
      else:
        start_col_offset = ' ' * start.col
        underline = '~' * (end.col - start.col)
        return f'{prev_line}{line}\n{start_col_offset}{underline}'
    else:
      all_lines = '\n'.join(lines[start.line:end.line + 1])
      start_col_offset = ' ' * start.col
      end_col_offset = ' ' * end.col
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
