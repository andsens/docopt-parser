from tests import chars, idents, maybe, indents, not_re, whitespaces
from hypothesis.strategies import one_of, just, text, from_regex, \
  tuples, none, composite, lists, integers, shared, booleans, \
  fixed_dictionaries, recursive
from hypothesis import settings, Verbosity
import re

settings(verbosity=Verbosity.verbose)

nl_indent = tuples(chars('\n'), indents).map(''.join)

def maybe_s(gen):
  return maybe(gen).flatmap(lambda res: just('') if res is None else just(res))

re_usage = re.compile(r'usage:', re.I)
re_options = re.compile(r'options:', re.I)
re_default = re.compile(r'\[default: [^\]]*\]', re.I)

other_text = text().filter(not_re(re_usage, re_options))
usage_title = from_regex(re_usage, fullmatch=True)

_wrapped_arg = idents('\n>').map(lambda s: f'<{s}>')
_uppercase_arg = from_regex(r'[A-Z0-9][A-Z0-9-]+', fullmatch=True)
_arg = one_of([_wrapped_arg, _uppercase_arg])

short_idents = chars(illegal='-=| \n()[],')
long_idents = idents(illegal='=| \n()[],', starts_with=chars(illegal='-=| \n()[]'))
_option = fixed_dictionaries({
  'ident': one_of(
    tuples(short_idents, none()),
    tuples(none(), long_idents),
  ),
  'has_arg': booleans(),
})

def partition_options_list(list_to_partition):
  known_shorts = [o['ident'][0] for o in list_to_partition if o['ident'][0] is not None]
  unused_short = short_idents.filter(lambda s: s not in known_shorts)
  known_longs = [o['ident'][1] for o in list_to_partition if o['ident'][1] is not None]
  unused_long = long_idents.filter(lambda s: s not in known_longs)

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
    usage = tuples() if index == 0 else tuples(*map(just, list_to_partition[0:index]))
    pos = index
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


_all_options = shared(lists(_option, unique_by=lambda o: o['ident']))

partitioned_options = shared(_all_options.flatmap(
  lambda all_opts: lists(
      integers(min_value=0, max_value=max(len(all_opts) - 1, 0)), unique=True
    ).flatmap(partition_options_list(all_opts))
))

usage_options = partitioned_options.flatmap(lambda p: just(p['usage']))


opt_arg = fixed_dictionaries({'sep': chars(' ='), 'ident': _arg})
option_doc_text = text(min_size=1).filter(not_re(re_usage, re_options, re_default))
documented_options = partitioned_options.flatmap(
  lambda partitions: tuples(*map(
    lambda options: tuples(*map(
      lambda opt: fixed_dictionaries({
          'indent': maybe(indents),
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
          'opt_sep': chars(', ') if o['short'] is not None and o['long'] is not None else none(),
          'doc_sep':
          text(alphabet=chars(' '), min_size=2) if o['default'] is not None or len(''.join(o['doc'])) > 0 else none(),
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

def to_usage_option(draw):
  def convert(o):
    short, long = o['ident']
    opt = f"-{short}" if short else f"--{long}"
    if o['has_arg']:
      a = draw(opt_arg)
      return f"{opt}{a['sep']}{a['ident']}"
    else:
      return opt
  return convert

@composite
def docopt_help(draw):
  uo = draw(usage_options)
  s_usage_options = ' '.join(map(to_usage_option(draw), uo))
  usage_section = f'{draw(usage_title)}{draw(maybe_s(nl_indent))}prog {s_usage_options}'
  s_option_sections = '\n\n'.join(draw(option_sections))
  return f'''{draw(other_text)}{usage_section}

{s_option_sections}'''


class AstNode(object):
  pass

  def indent(self, node, lvl=1):
    if isinstance(node, list):
      lines = '\n'.join(map(repr, node)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
    else:
      lines = repr(node).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)

class IdentNode(AstNode):
  def __hash__(self):
    return hash(self.ident)

class PlainOption(IdentNode):
  def __init__(self, short, long, has_arg):
    if short:
      self.ident = short
      self.type = '-'
    else:
      self.ident = long
      self.type = '--'
    self.has_arg = has_arg

  def __repr__(self):
    arg = ' <ARG>' if self.has_arg else ''
    return f'<PlainOption>: {self.type}{self.ident}{arg}'

  options = one_of(
    tuples(short_idents, none(), booleans()),
    tuples(none(), long_idents, booleans()),
  ).map(lambda o: PlainOption(*o))


class Command(IdentNode):
  def __init__(self, ident):
    self.ident = ident

  def __repr__(self):
    return f'<Command>: {self.ident}'

  def __str__(self):
    return f"{self.ident}"

  commands = idents('| \n[]()', starts_with=chars(illegal='-| \n[]()')).map(lambda c: Command(c))

class Argument(IdentNode):
  def __init__(self, ident):
    self.ident = ident

  def __repr__(self):
    return f'<Argument>: {self.ident}'

  def __str__(self):
    return self.ident

  wrapped_args = idents('\n>').map(lambda s: f'<{s}>')
  uppercase_args = from_regex(r'[A-Z0-9][A-Z0-9-]+', fullmatch=True)
  args = one_of(wrapped_args, uppercase_args).map(lambda a: Argument(a))

class ArgumentSeparator(AstNode):
  def __repr__(self):
    return '<ArgumentSeparator>'

  def __str__(self):
    return '--'

  separators = just('--').map(lambda _: ArgumentSeparator())

class OptionsShortcut(AstNode):
  def __repr__(self):
    return '<OptionsShortcut>'

  def __str__(self):
    return 'options'

  shortcuts = just('options').map(lambda _: OptionsShortcut())

class Choice(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f'''<Choice>
{self.indent(self.items)}'''

  eithers = tuples(text(alphabet=chars(' ')), chars('|'), text(alphabet=chars(' '))).map(''.join)

  def __str__(self):
    if len(self.items) > 1:
      return f"({'|'.join(map(str, self.items))})"
    else:
      return str(self.items[0])

class Sequence(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f"""<Sequence>
{self.indent(self.items)}"""

  def __str__(self):
    return ' '.join(map(str, self.items))

class Optional(AstNode):
  def __init__(self, items):
    self.items = items

  def __repr__(self):
    return f"""<Optional>
  {self.indent(self.items)}"""

  def __str__(self):
    return f"[{' '.join(map(str, self.items))}]"

class Usage(AstNode):
  def __init__(self, root):
    self.root = root

  def __repr__(self):
    return f"""<Usage>
  {self.indent(self.root)}"""

  def __str__(self):
    if type(self.root) is list:
      lines = '\n'.join(map(lambda line: f'  prog {line}', map(str, self.root)))
    else:
      lines = f'  prog {str(self.root)}'
    return f"""Usage:
{lines}
"""

  usages = recursive(
    lists(one_of(
      ArgumentSeparator.separators,
      Command.commands,
      Argument.args,
      OptionsShortcut.shortcuts
    ), min_size=1),
    lambda items: one_of(
      just(Choice),
      just(Sequence),
      just(Optional),
    ).flatmap(lambda N: items.map(lambda i: N(i) if type(i) is list else N([i])))
  ).map(lambda n: Usage(n))

if __name__ == "__main__":
  import sys
  sys.ps1 = '>>>'
  print(Usage.usages.example())
