from hypothesis.strategies import one_of, characters, just, text, from_regex, \
  sets, tuples, none, composite, lists, sampled_from, integers
from hypothesis import settings, Verbosity
import re
from functools import reduce

settings(verbosity=Verbosity.verbose)

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

def chars(legal=None, illegal=None, **kwargs):
  if (legal is None) == (illegal is None):
    raise Exception('chars(): legal and illegal parameters are mutually exclusive')
  if legal is not None:
    return text(alphabet=char(legal=legal), **kwargs)
  else:
    return text(alphabet=char(illegal=illegal), **kwargs)

def ident(illegal, starts_with=None):
  if starts_with is not None:
    return tuples(starts_with, chars(illegal=illegal)).map(lambda t: ''.join(t))
  else:
    return chars(illegal=illegal, min_size=1)

nl = char('\n')
indent = one_of(chars(' ', min_size=1), char('\t'))
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

other_text = text().filter(not_re(re_usage, re_options))
usage_title = from_regex(re_usage, fullmatch=True)
options_title = from_regex(re_options, fullmatch=True)

wrapped_arg = ident('\n>').map(lambda s: f'<{s}>')
uppercase_arg = from_regex(r'[A-Z0-9][A-Z0-9-]+', fullmatch=True)
arg = one_of([wrapped_arg, uppercase_arg])

short_ident = char(illegal='-=| \n()[]')
long_ident = ident(illegal='=| \n()[]', starts_with=char(illegal='-=| \n()[]'))
option = tuples(
  one_of(none(), short_ident),
  one_of(none(), long_ident),
).filter(lambda x: x[0] is not None or x[1] is not None)


def partition_list(list_to_partition):
  def partition(indices):
    lists = []
    pos = 0
    for index in sorted(indices):
      lists.append(list_to_partition[pos:index])
      pos = index
    return lists
  return partition


options = lists(option, unique_by=(lambda s: s[0], lambda s: s[1]), min_size=5).flatmap(
  lambda all_options: lists(
    integers(min_value=0, max_value=max(len(all_options) - 1, 0)), unique=True, min_size=1
  ).map(partition_list(all_options))
)

option_line_doc_sep = text(alphabet=char(' '), min_size=2)
option_doc_text = text().filter(not_re(re_usage, re_options, re_default))
opt_arg_sep = char(' =')
opt_sep = char(', ')
default = one_of(none(), text().filter(not_re(re_usage, re_options)))

def to_usage_option(o):
  short, long = o
  if short and long:
    return f'(-{short}|--{long})'
  if short:
    return f'-{short}'
  if long:
    return f'--{long}'

@composite
def docopt_help(draw):
  usage_options, *options_sections_options = draw(options)
  s_usage_options = ' '.join(map(to_usage_option, usage_options))
  usage_section = f'{draw(usage_title)}{draw(maybe(nl_indent))}prog {s_usage_options}'
  option_sections = []
  for options_section_options in options_sections_options:
    elements = []
    for i, opt in enumerate(options_section_options):
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
      opt_doc = []
      opt_doc.append(draw(option_doc_text))
      if s_default:
        opt_doc.append(f'[default: {s_default}]')
      opt_doc.append(draw(option_doc_text))
      s_opt_doc = ''.join(opt_doc)
      if len(s_opt_doc) > 0:
        elements.append(draw(chars(' ', min_size=2)))
        elements.append(s_opt_doc)
      else:
        elements.append(draw(chars(' ')))
      if i < len(options_section_options) - 1:
        elements.append(draw(nl_indent))
    option_sections.append(f'{draw(options_title)}{draw(maybe(nl_indent))}{"".join(elements)}')
  s_option_sections = '\n\n'.join(option_sections)
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
