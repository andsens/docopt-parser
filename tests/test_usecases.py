from . import Usecase
from docopt_parser.parser import parse_doc


def test_usecase(usecase):
  assert usecase == run_usecase(usecase)


def run_usecase(usecase):
  file, lineno, doc, _ = usecase
  result = parse_doc(doc)
  return Usecase(file, lineno, doc, result)
