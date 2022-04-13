from functools import total_ordering
from parsec import ParseError

MarkedTuple = tuple[tuple[int, int], str, tuple[int, int]]

@total_ordering
class Location(object):
  line: int
  col: int

  def __init__(self, loc: tuple[int, int]):
    self.line, self.col = loc

  def __eq__(self, other: tuple[int, int]):
    return self.line == other.line and self.col == other.col

  def __lt__(self, other):
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
    self.start = start
    self.end = end

  def __eq__(self, other: Location):
    return self.start == other.start and self.end == other.end

  def __lt__(self, other):
    return self.start < other.start or (self.start == other.start and self.end < other.end)

  def show(self, text: str):
    lines = text.split('\n')
    if self.start.line == self.end.line:
      if self.start.line > 0:
        prev_line = lines[self.start.line - 1]
      line = lines[self.start.line]
      if line.strip() == line[self.start.col:self.end.col].strip():
        return f'\n{prev_line}\n{line} <---'
      else:
        start_col_offset = ' ' * self.start.col
        underline = '~' * (self.end.col - self.start.col)
        return f'\n{prev_line}\n{line}\n{start_col_offset}{underline}'
    else:
      all_lines = '\n'.join(lines[self.start.line:self.end.line])
      start_col_offset = ' ' * self.start.col
      end_col_offset = ' ' * self.end.col
      return f'\n{start_col_offset}V\n{all_lines}\n{end_col_offset}^'

class Marked(Mark):
  txt: str

  def __init__(self, mark: MarkedTuple):
    start, txt, end = mark
    super().__init__(Location(start), Location(end))
    self.txt = txt


def explain_error(e: ParseError, text: str) -> str:
  loc = Location(e.loc_info(e.text, e.index))
  return f'\n{loc.show(text)}^\n{str(e)}'
