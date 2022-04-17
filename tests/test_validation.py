import warnings
import pytest
from docopt_parser import parse, doc
import unittest
import re


def test_used_options():
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    parse('''Usage:
  prog -f

Options:
  -f, --long
''')

def test_unused_options():
  with pytest.warns(UserWarning, match=re.escape('<--- this option is not referenced from the usage section.')):
    parse('''Usage:
  prog

Options:
  -f
''')

def test_duplicate_options():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('-f has already been specified on line 5')):
    parse('''Usage:
  prog options

Options:
  -f
  -f
''')

def test_missing_arg_from_doc():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('-a expects an argument')):
    parse('''Usage:
  prog -a

Options:
  -a=B
''')

def test_missing_arg_from_usage():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('--long expects an argument')):
    parse('''Usage:
  prog --long=F
  prog --long
''')

def test_unexpected_arg_from_doc():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('--long does not expect an argument')):
    parse('''Usage:
  prog --long=B

Options:
  --long
''')

def test_unexpected_arg_from_usage():
  with pytest.raises(doc.DocoptParseError, match=r'.*' + re.escape('--long does not expect an argument')):
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
