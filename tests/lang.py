from hypothesis.strategies import one_of, characters, just, text, from_regex, \
  sets, tuples, none, composite, lists, sampled_from, integers
import re
from functools import reduce

def char(legal=None, illegal=None):
  if (legal is None) == (illegal is None):
    raise Exception('char(): legal and illegal parameters are mutually exclusive')
  if legal is not None:
    if len(legal) == 1:
      return just(legal)
    else:
      return sampled_from(legal)
  else:
    return characters(blacklist_characters=illegal)

def chars(legal=None, illegal=None):
  if (legal is None) == (illegal is None):
    raise Exception('chars(): legal and illegal parameters are mutually exclusive')
  if legal is not None:
    return text(alphabet=char(legal=legal))
  else:
    return text(alphabet=char(illegal=illegal))

nl = char('\n')
spaces = lists(char(' '), min_size=1).map(''.join)
indent = one_of(spaces, char('\t'))
nl_indent = tuples(nl, indent).map(''.join)
def maybe(gen):
  return one_of(just(''), gen)

re_usage = re.compile(r'usage:', re.I)
re_options = re.compile(r'options:', re.I)
re_default = re.compile(r'\[default: [^\]]*\]', re.I)
def not_re(*args):
  def check(s):
    return all((r.search(s) is None for r in args))
  return check

def ident(illegal, starts_with=None):
  @composite
  def gen(draw):
    start = legal = characters(blacklist_characters=illegal)
    if starts_with is not None:
      start = starts_with
    return f'{draw(start)}{draw(legal)}'
  return gen()

other_text = text().filter(not_re(re_usage, re_options))
usage_title = from_regex(re_usage, fullmatch=True)
options_title = from_regex(re_options, fullmatch=True)

wrapped_arg = ident('\n>').map(lambda s: f'<{s}>')
uppercase_arg = from_regex(r'[A-Z0-9][A-Z0-9-]+', fullmatch=True)
arg = one_of([wrapped_arg, uppercase_arg])

short_ident = characters(blacklist_characters='-=')
long_ident = text(alphabet=characters(blacklist_characters='-'), min_size=2)
option = tuples(
  one_of(none(), short_ident),
  one_of(none(), long_ident),
).filter(lambda x: x[0] is not None or x[1] is not None)
section_partitions = lists(integers(min_value=0, max_value=20), min_size=1, max_size=20)
option_line_doc_sep = text(alphabet=char(' '), min_size=2)
option_doc_text = text().filter(not_re(re_usage, re_options, re_default))
opt_arg_sep = char(' =')
opt_sep = char(', ')
default = one_of(none(), text().filter(not_re(re_usage, re_options)))

def to_usage_option(o):
  short, long = o
  if short and long:
    return '(-{short}|--{long})'
  if short:
    return '-{short}'
  if long:
    return '-{long}'

@composite
def docopt_help(draw):
  section_sizes = draw(section_partitions)
  total = reduce(lambda mem, n: mem + n, section_sizes)
  options = draw(lists(option, unique_by=(lambda s: s[0], lambda s: s[0]), min_size=total, max_size=total))
  pos = 0
  usage_options = options[pos:(pos + section_sizes[0])]
  s_usage_options = ' '.join(map(to_usage_option, usage_options))
  usage_section = f'{draw(usage_title)}{draw(maybe(nl_indent))}prog {s_usage_options}'
  pos += section_sizes[0]
  option_sections = []
  for size in section_sizes[1:]:
    elements = []
    for i, opt in enumerate(options[pos:(pos + size)]):
      short, long = opt
      s_default = draw(default)
      if short:
        opt_arg = draw(arg)
        if arg:
          elements.append(f'-{short}{draw(opt_arg_sep)}{opt_arg}')
        else:
          elements.append(f'-{short}')
        if long:
          elements.append(draw(opt_sep))
      if long:
        opt_arg = draw(arg)
        if opt_arg:
          elements.append(f'--{long}{draw(opt_arg_sep)}{opt_arg}')
        else:
          elements.append(f'--{long}')
      elements.append(draw(option_doc_text))
      if s_default:
        elements.append(f'[default: {s_default}]')
      elements.append(draw(option_doc_text))
      if i < size - 1:
        elements.append(draw(maybe(nl_indent)))
    option_sections.append(f'{draw(options_title)}{draw(maybe(nl_indent))}{"".join(elements)}')
    pos += size
  s_option_sections = '\n'.join(option_sections)
  return f'''{draw(other_text)}{usage_section}
{s_option_sections}'''


arguments = sets(arg)
command = ident('\n', characters(blacklist_characters='-\n'))
argument_separator = just('--')

# strategies.recursive(base, extend, *, max_leaves=100)
# hypothesis.strategies.sampled_from(elements)

if __name__ == "__main__":
  import sys
  sys.ps1 = '>>>'
  print(docopt_help().example())
