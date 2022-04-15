from functools import total_ordering
from typing import Generic, List, Tuple, TypeVar
from parsec import ParseError

T = TypeVar('T')
LocInfo = Tuple[int, int]
MarkedTuple = Tuple[LocInfo, T, LocInfo]

# All text editors use 1 indexed lines, so we simply subclass int for linenumbers
class LineNumber(int):
  def __str__(self):
    return str(self + 1)

  def __repr__(self):
    return str(self + 1)

  def show(self, text: List[str] | str):
    lines = text if isinstance(text, list) else text.split('\n')
    return f'{(self + 1):02d} {lines[self]}'

  @property
  def prefix_length(self):
    return len(f'{(self + 1):02d} ')

@total_ordering
class Location(object):
  line: LineNumber
  col: int

  def __init__(self, loc: LocInfo):
    super().__init__()
    self.line = LineNumber(loc[0])
    self.col = loc[1]

  def __eq__(self, other: object):
    return isinstance(other, Location) and self.line == other.line and self.col == other.col

  def __lt__(self, other: object):
    if not isinstance(other, Location):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.line < other.line or (self.line == other.line and self.col < other.col)

  def __repr__(self):
    return f'{self.line}:{self.col}'

  def show(self, text: List[str] | str):
    col_offset = ' ' * self.col
    return f'{self.line.show(text)}\n{col_offset}^'

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

  def show(self, text: str, message: str | None = None):
    lines = text.split('\n')
    start = Location((self.start.line, self.start.col))
    end = Location((self.end.line, self.end.col))
    # If "end" is at column 0 on a new line,
    # move the location back to the end of the previous line.
    if end.col == 0 and end > start:
      end.line = LineNumber(end.line - 1)
      end.col = len(lines[end.line])
    if start.line == end.line:
      line = lines[start.line]
      if line.strip() == line[start.col:end.col].strip():
        message = f' <--- {message}' if message is not None else ''
        return f'{start.line.show(lines)}{message}'
      else:
        start_col_offset = ' ' * (start.col + start.line.prefix_length)
        underline = '~' * (end.col - start.col)
        message = f'\n{message}' if message is not None else ''
        return f'{start.line.show(lines)}\n{start_col_offset}{underline}{message}'
    else:
      # i + 1 accounts for editor line numbering
      # end.line + 1 accounts for [a,b,c][1,2] = [b] and not [b,c] (end.line is be inclusive)
      all_lines = '\n'.join(LineNumber(i).show(lines) for i in range(start.line, end.line + 1))
      start_col_offset = ' ' * (start.col + start.line.prefix_length)
      end_col_offset = ' ' * (end.col + end.line.prefix_length)
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
