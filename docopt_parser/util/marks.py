from dataclasses import dataclass
import typing as T
from functools import total_ordering

from docopt_parser.util import errors

_T = T.TypeVar('_T')
LocInfo = T.Tuple[int, int]
RangeTuple = T.Tuple[LocInfo, LocInfo]
MarkedTuple = T.Tuple[LocInfo, _T, LocInfo]

class ByteCount(int):

  def show(self, text: T.List[str] | str, message: str | None = None):
    lines = text if isinstance(text, list) else text.split('\n')
    return self.to_location(lines).show(lines, message)

  def to_location(self, text: T.List[str] | str) -> "Location":
    lines = text if isinstance(text, list) else text.split('\n')
    count = self
    for line_no, line in enumerate(lines):
      length = len(line) + 1
      if length > count:
        return Location((line_no, count))
      count -= length
    raise errors.DocoptError(f'Unable to convert bytecount {self} into location with the given text')

# All text editors use 1 indexed lines, so we simply subclass int for linenumbers
class LineNumber(int):
  def __str__(self):
    return str(self + 1)

  def __repr__(self):
    return str(self + 1)

  def show(self, text: "T.List[str] | str"):
    lines = text if isinstance(text, list) else text.split('\n')
    return f'{(self + 1):02d} {lines[self]}'

  @property
  def prefix_length(self):
    return len(f'{(self + 1):02d} ')

@total_ordering
@dataclass(frozen=True, init=False, eq=False, repr=False)
class Location:
  line: LineNumber
  col: int

  def __init__(self, loc: LocInfo):
    super().__init__()
    object.__setattr__(self, 'line', LineNumber(loc[0]))
    object.__setattr__(self, 'col', loc[1])

  def __eq__(self, other: object):
    return isinstance(other, Location) and self.line == other.line and self.col == other.col

  def __lt__(self, other: object):
    if not isinstance(other, Location):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.line < other.line or (self.line == other.line and self.col < other.col)

  def __repr__(self):
    return f'{self.line}:{self.col}'

  def to_tuple(self):
    return (self.line, self.col)

  def to_bytecount(self, text: "T.List[str] | str") -> int:
    lines = text if isinstance(text, list) else text.split('\n')
    return sum(len(line) for line in lines[0:self.line]) + self.line + self.col

  def show(self, text: "T.List[str] | str", message: "str | None" = None):
    message = f'\n{message}' if message is not None else ''
    col_offset = ' ' * (self.col + self.line.prefix_length)
    return f'{self.line.show(text)}\n{col_offset}^{message}'

@total_ordering
@dataclass(frozen=True, eq=False)
class Range:
  start: Location
  end: Location

  def __init__(self, range: RangeTuple):
    super().__init__()
    object.__setattr__(self, 'start', Location(range[0]))
    object.__setattr__(self, 'end', Location(range[1]))

  def __eq__(self, other: object):
    return isinstance(other, Range) and self.start == other.start and self.end == other.end

  def __lt__(self, other: object):
    if not isinstance(other, Range):
      raise Exception(f'Unable to compare <Location> with <{type(other)}>')
    return self.start < other.start or (self.start == other.start and self.end < other.end)

  def __repr__(self):
    return f'{self.start}-{self.end}'

  def to_bytecount(self, text: "T.List[str] | str") -> T.Tuple[int, int]:
    lines = text if isinstance(text, list) else text.split('\n')
    return (self.start.to_bytecount(lines), self.end.to_bytecount(lines))

  def wrap_element(self, elm: _T) -> "Marked[_T]":
    return Marked(((self.start.line, self.start.col), elm, (self.end.line, self.end.col)))

  def to_range_tuple(self) -> RangeTuple:
    return ((self.start.line, self.start.col), (self.end.line, self.end.col))

  def __lshift__(self, other: _T) -> MarkedTuple[_T]:
    # Returns a MarkedTuple with other as the element
    return ((self.start.line, self.start.col), other, (self.end.line, self.end.col))


  def show(self, text: str, message: "str | None" = None):
    lines = text.split('\n')
    start = Location((self.start.line, self.start.col))
    end = Location((self.end.line, self.end.col))
    # If "end" is at column 0 on a new line,
    # move the location back to the end of the previous line.
    if end.col == 0 and end > start:
      end = Location((end.line - 1, len(lines[end.line])))
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

@dataclass(frozen=True)
class Marked(Range, T.Generic[_T]):
  elm: _T

  def __init__(self, mark: MarkedTuple[_T]):
    super().__init__((mark[0], mark[2]))
    object.__setattr__(self, 'elm', mark[1])
