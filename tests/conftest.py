import logging
import os
import re
import glob
import json
import itertools
from . import Usecase

log = logging.getLogger(__name__)


def pytest_generate_tests(metafunc):
  if 'usecase' in metafunc.fixturenames:
    usecase_generators = []
    for path in glob.glob(os.path.join(os.path.dirname(__file__), '*-parser-usecases.txt')):
      usecase_generators.append(parse_usecases(path))
    cases, copied_cases = itertools.tee(itertools.chain(*usecase_generators))
    ids = ('%s:%d' % (case.file, case.line) for case in copied_cases)
    metafunc.parametrize('usecase', cases, ids=ids)


def pytest_assertrepr_compare(config, op, left, right):
  if isinstance(left, Usecase) and isinstance(right, Usecase) and op == '==':
    error = ['Usecase in %s:%d failed' % (left.file, left.line)]
    error.append('%s' % left.doc)
    if isinstance(left.expect, str) or isinstance(right.expect, str):
      error.append('%s != %s' % (repr(left.expect), repr(right.expect)))
    else:
      for key, value in left.expect.items():
        if key in right.expect:
          if value != right.expect[key]:
            error.append('%s != %s' % (repr(value), repr(right.expect[key])))
        else:
          error.append('%s != (key %s not found)' % (repr(value), key))
      for key, value in right.expect.items():
        if key not in left.expect:
          error.append('(key %s not found) != %s' % (key, repr(value)))
    return error


def parse_usecases(path):
  with open(path, 'r') as handle:
    raw = handle.read()
  usecase_pattern = re.compile(r'r"""(?P<doc>.+?)"""(?P<expect>(\{\n|.)+?\})', re.DOTALL)
  file = os.path.basename(path)
  for usecase_match in usecase_pattern.finditer(raw):
    line = raw[:usecase_match.start('doc')].count('\n') + 1
    doc = usecase_match.group('doc')
    expect_raw = usecase_match.group('expect')
    try:
      expect = json.loads(usecase_match.group('expect'))
    except json.decoder.JSONDecodeError as e:
      json_line = raw[:usecase_match.start('expect')].count('\n')
      raise Exception('Error on line %d:\n%s\n---\n%s' % (json_line, expect_raw, str(e)))
    yield Usecase(file, line, doc, expect)
    break
