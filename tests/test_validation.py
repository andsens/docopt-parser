import warnings
import pytest as PT
from docopt_parser import parse, DocoptError
import unittest
import re


def test_used_options():
  parse('''Usage:
  prog -f

Options:
  -f, --long
''')

def test_unused_options(caplog: PT.LogCaptureFixture):
  parse('''Usage:
  prog

Options:
  -f
''')
  assert '-f is not referenced from the usage section' in caplog.text

def test_duplicate_options():
  with PT.raises(DocoptError, match=r'.*' + re.escape('-f has already been specified') + r'.*'):
    parse('''Usage:
  prog options

Options:
  -f
  -f
''')

def test_missing_arg_from_doc():
  with PT.raises(DocoptError, match=r'.*' + re.escape('expected: argument at') + r'.*'):
    parse('''Usage:
  prog -a

Options:
  -a=B
''')

def test_missing_arg_from_usage():
  with PT.raises(DocoptError, match=r'.*' + re.escape('expected: argument at') + r'.*'):
    parse('''Usage:
  prog --long=F
  prog --long
''')

def test_unexpected_arg_from_doc():
  with PT.raises(DocoptError, match=r'.*' + re.escape('--long does not expect an argument')):
    parse('''Usage:
  prog --long=B

Options:
  --long
''')

def test_unexpected_arg_from_usage():
  with PT.raises(DocoptError, match=r'.*' + re.escape('--long does not expect an argument')):
    parse('''Usage:
  prog --long
  prog --long=B
''')


def test_repated_option_with_arg():
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    parse('''Usage:
  prog -f B...

Options:
  -f ARG
''')

if __name__ == "__main__":
  unittest.main()
