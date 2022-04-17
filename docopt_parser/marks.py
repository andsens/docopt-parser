import typing as T
from functools import total_ordering
from parsec import ParseError

_T = T.TypeVar('_T')
LocInfo = T.Tuple[int, int]
RangeTuple = T.Tuple[LocInfo, LocInfo]
MarkedTuple = T.Tuple[LocInfo, _T, LocInfo]

# All text editors use 1 indexed lines, so we simply subclass int for linenumbers
class LineNumber(int):
  def __str__(self):
    return str(self + 1)

  def __repr__(self):
    return str(self + 1)

  def show(self, text: T.List[str] | str):
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

  def show(self, text: T.List[str] | str, message: str | None = None):
    message = f'\n{message}' if message is not None else ''
    col_offset = ' ' * (self.col + self.line.prefix_length)
    return f'{self.line.show(text)}\n{col_offset}^{message}'

@total_ordering
class Range(object):
  start: Location
  end: Location

  def __init__(self, range: RangeTuple):
    super().__init__()
    self.start = Location(range[0])
    self.end = Location(range[1])

  def __eq__(self, other: object):
    return isinstance(other, Range) and self.start == other.start and self.end == other.end

  def __lt__(self, other: object):
    if not isinstance(other, Range):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.start < other.start or (self.start == other.start and self.end < other.end)

  def __repr__(self):
    return f'{self.start}-{self.end}'

  def wrap_element(self, elm: _T) -> "Marked[_T]":
    return Marked(((self.start.line, self.start.col), elm, (self.end.line, self.end.col)))

  def to_range_tuple(self) -> RangeTuple:
    return ((self.start.line, self.start.col), (self.end.line, self.end.col))

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

class Marked(Range, T.Generic[_T]):
  elm: _T

  def __init__(self, mark: MarkedTuple[_T]):
    super().__init__((mark[0], mark[2]))
    self.elm = mark[1]

  def to_marked_tuple(self) -> MarkedTuple[_T]:
    return ((self.start.line, self.start.col), self.elm, (self.end.line, self.end.col))


def explain_error(e: ParseError, text: str) -> str:
  (line, col) = e.loc_info(e.text, e.index)
  loc = Location((line, col))
  return f'{loc.show(text)}\n{str(e)}'
