from docopt_parser.util import marks

class DocoptError(Exception):
  def __init__(self, message: str, exit_code: int = 1):
    super().__init__(message)
    self.message = message
    self.exit_code = exit_code

class DocoptParseError(DocoptError):
  mark: "marks.Location | marks.Range | marks.ByteCount | None"

  def __init__(self, message: str, mark: "marks.Location | marks.Range | marks.ByteCount | None" = None):
    super().__init__(message, 1)
    self.mark = mark
