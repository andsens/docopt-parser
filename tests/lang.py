from hypothesis.strategies import one_of, characters, just, text, from_regex, \
  sets, tuples, none, composite, lists, sampled_from, integers, shared, booleans, \
  fixed_dictionaries
from hypothesis import settings, Verbosity
import re

settings(verbosity=Verbosity.verbose)

# pluralize strategies, like hypothesis

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
  return one_of(none(), gen)

def maybe_s(gen):
  return maybe(gen).flatmap(lambda res: just('') if res is None else just(res))

re_usage = re.compile(r'usage:', re.I)
re_options = re.compile(r'options:', re.I)
re_default = re.compile(r'\[default: [^\]]*\]', re.I)
def not_re(*args):
  def check(s):
    return all((r.search(s) is None for r in args))
  return check

other_text = text().filter(not_re(re_usage, re_options))
usage_title = from_regex(re_usage, fullmatch=True)

wrapped_arg = ident('\n>').map(lambda s: f'<{s}>')
uppercase_arg = from_regex(r'[A-Z0-9][A-Z0-9-]+', fullmatch=True)
arg = one_of([wrapped_arg, uppercase_arg])

short_ident = char(illegal='-=| \n()[]')
long_ident = ident(illegal='=| \n()[]', starts_with=char(illegal='-=| \n()[]'))
option = fixed_dictionaries({
  'ident': one_of(
    tuples(short_ident, none()),
    tuples(none(), long_ident),
  ),
  'has_arg': booleans(),
})

def partition_options_list(list_to_partition):
  known_shorts = [o['ident'][0] for o in list_to_partition if o['ident'][0] is not None]
  unused_short = short_ident.filter(lambda s: s not in known_shorts)
  known_longs = [o['ident'][1] for o in list_to_partition if o['ident'][1] is not None]
  unused_long = long_ident.filter(lambda s: s not in known_longs)

  @composite
  def add_alt_opt(draw, o):
    short, long = o['ident']
    if short is None:
      _short = draw(maybe(unused_short))
      if _short is not None:
        known_shorts.append(short)
      return {
        'short': None if _short is None else {
          'ident': _short,
          'has_arg': draw(booleans()) if o['has_arg'] else False
        },
        'long': {'ident': long, 'has_arg': o['has_arg']},
        'has_arg': o['has_arg'],
      }
    if long is None:
      _long = draw(maybe(unused_long))
      if _long is not None:
        known_longs.append(_long)
      return {
        'short': {'ident': short, 'has_arg': o['has_arg']},
        'long': None if _long is None else {
          'ident': _long,
          'has_arg': draw(booleans()) if o['has_arg'] else False
        },
        'has_arg': o['has_arg'],
      }

  def partition(indices):
    if len(indices) == 0:
      return fixed_dictionaries({
        'usage': tuples(),
        'options': tuples()
      })
    index, *indices = sorted(indices)
    pos = 0
    usage = tuples() if pos == index else tuples(*map(just, list_to_partition[pos:index]))
    lists = []
    for index in indices:
      lists.append(tuples() if pos == index else tuples(*map(add_alt_opt, list_to_partition[pos:index])))
      pos = index
    lists.append(tuples() if pos == len(list_to_partition) - 1 else tuples(*map(add_alt_opt, list_to_partition[pos:])))
    return fixed_dictionaries({
      'usage': usage,
      'options': tuples(*lists)
    })
  return partition


all_options = shared(lists(option, unique_by=lambda o: o['ident']))

partitioned_options = shared(all_options.flatmap(
  lambda all_opts: lists(
      integers(min_value=0, max_value=max(len(all_opts) - 1, 0)), unique=True
    ).flatmap(partition_options_list(all_opts))
))

usage_options = partitioned_options.flatmap(lambda p: just(p['usage']))


opt_arg = fixed_dictionaries({'sep': char(' ='), 'ident': arg})
option_doc_text = text(min_size=1).filter(not_re(re_usage, re_options, re_default))
documented_options = partitioned_options.flatmap(
  lambda partitions: tuples(*map(
    lambda options: tuples(*map(
      lambda opt: fixed_dictionaries({
          'indent': maybe(indent),
          'short': fixed_dictionaries({
            'ident': just(opt['short']['ident']),
            'arg': opt_arg if opt['short']['has_arg'] else none()
          }) if opt['short'] is not None else none(),
          'long': fixed_dictionaries({
            'ident': just(opt['long']['ident']),
            'arg': opt_arg if opt['long']['has_arg'] else none()
          }) if opt['long'] is not None else none(),
          'doc': tuples(option_doc_text, option_doc_text),
          'default': maybe(text().filter(not_re(re_usage, re_options))) if opt['has_arg'] else none(),
        }).flatmap(lambda o: fixed_dictionaries({
          **{k: just(v) for k, v in o.items()},
          'opt_sep': char(', ') if o['short'] is not None and o['long'] is not None else none(),
          'doc_sep':
          text(alphabet=char(' '), min_size=2) if o['default'] is not None or len(''.join(o['doc'])) > 0 else none(),
        })),
      options
    )) if len(options) > 0 else tuples(),
    partitions['options']))
)

option_sections = documented_options.flatmap(
  lambda sections: tuples(*map(
    lambda options: fixed_dictionaries({
      'title': from_regex(re_options, fullmatch=True),
      'lines': just(map(
          lambda opt: ''.join([
            opt['indent'] if opt['indent'] else '',
            f"-{opt['short']['ident']}" if opt['short'] else '',
            opt['short']['arg']['sep'] if opt['short'] and opt['short']['arg'] else '',
            opt['short']['arg']['ident'] if opt['short'] and opt['short']['arg'] else '',
            opt['opt_sep'] if opt['opt_sep'] else '',
            f"--{opt['long']['ident']}" if opt['long'] else '',
            opt['long']['arg']['sep'] if opt['long'] and opt['long']['arg'] else '',
            opt['long']['arg']['ident'] if opt['long'] and opt['long']['arg'] else '',
            opt['doc_sep'] if opt['doc_sep'] else '',
            opt['doc'][0] if opt['doc'] else '',
            f"[default: {opt['default']}]" if opt['default'] else '',
            opt['doc'][1] if opt['doc'] else '',
          ]),
          options))
    }),
    sections)) if len(sections) > 0 else tuples()
).map(
  lambda sections: map(
    lambda section: '\n'.join([section['title']] + list(section['lines'])),
    sections
  )
)

def to_usage_option(o):
  short, long = o['ident']
  if short:
    return f"-{short}"
  if long:
    return f"--{long}"

@composite
def docopt_help(draw):
  uo = draw(usage_options)
  s_usage_options = ' '.join(map(to_usage_option, uo))
  usage_section = f'{draw(usage_title)}{draw(maybe_s(nl_indent))}prog {s_usage_options}'
  s_option_sections = '\n\n'.join(draw(option_sections))
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
