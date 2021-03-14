from typing import Iterable
from tests import chars, idents, maybe, indents, not_re, whitespaces
from hypothesis.strategies import one_of, just, text, from_regex, \
  tuples, none, composite, lists, integers, shared, booleans, \
  fixed_dictionaries, recursive, sampled_from
from hypothesis import settings, Verbosity
from functools import reduce
from itertools import repeat, chain
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

short_idents = chars(illegal='-=| \n()[],')
long_idents = idents(illegal='=| \n()[],', starts_with=chars(illegal='-=| \n()[]'))


class AstNode(object):
  pass

  def indent(self, node, lvl=1):
    if isinstance(node, Iterable):
      lines = '\n'.join(map(repr, node)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
    else:
      lines = repr(node).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)

class IdentNode(AstNode):
  def __hash__(self):
    return hash(self.ident)

def partitioned_options(sizes):
  known_shorts = []
  unused_shorts = short_idents.filter(lambda s: s not in known_shorts)
  known_longs = []
  unused_longs = long_idents.filter(lambda s: s not in known_longs)

  def register_drawn(o):
    short, long, _ = o
    if short:
      known_shorts.append(short)
    if long:
      known_longs.append(long)
    return just(o)

  usage_options = one_of(
    tuples(unused_shorts, none(), booleans()),
    tuples(none(), unused_longs, booleans()),
  ).flatmap(register_drawn).map(lambda o: UsageOption(*o))

  documented_options = one_of(
    tuples(unused_shorts, none(), booleans()),
    tuples(none(), unused_longs, booleans()),
    tuples(unused_shorts, unused_longs, booleans()),
  ).flatmap(register_drawn).map(lambda o: DocumentedOption(*o))

  usage_size, *options_sizes = sizes
  return fixed_dictionaries({
    'usage': lists(usage_options, min_size=usage_size, max_size=usage_size),
    'documented': tuples(*map(
      lambda size: lists(documented_options, min_size=size, max_size=size),
      options_sizes
    ))
  })

section_sizes = lists(
  integers(min_value=0, max_value=20), min_size=3, unique=True
).map(lambda indices: reduce(lambda sizes, i: sizes + [i - sum(sizes)], sorted(indices), []))

all_options = shared(section_sizes.flatmap(partitioned_options))
usage_options = all_options.flatmap(lambda p: just(p['usage']))
documented_options = all_options.flatmap(lambda p: just(p['documented']))

class UsageOption(AstNode):
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
    return f'<Option>: {self.type}{self.ident}{arg}'

  def __str__(self):
    arg = ' <ARG>' if self.has_arg else ''
    return f'{self.type}{self.ident}{arg}'

class DocumentedOption(AstNode):
  def __init__(self, short, long, has_arg):
    self.short = short
    self.long = long
    self.has_arg = has_arg

  def __repr__(self):
    arg = ' <ARG>' if self.has_arg else ''
    short = f'-{self.short}' if self.short else ''
    long = f'--{self.long}' if self.long else ''
    ident = f'{short}, {long}' if self.short and self.long else short or long
    return f'<Option>: {ident}{arg}'

  def __str__(self):
    arg = ' <ARG>' if self.has_arg else ''
    short = f'-{self.short}' if self.short else ''
    long = f'--{self.long}' if self.long else ''
    ident = f'{short}, {long}' if self.short and self.long else short or long
    return f'{ident}{arg}'

  def usage_ref(self):
    arg = ' <ARG>' if self.has_arg else ''
    ident = f'-{self.short}' if self.short else f'--{self.long}'
    return f'{ident}{arg}'

class OptionRef(AstNode):
  def __init__(self, option):
    self.option = option

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.option)}'''

  def __str__(self):
    return self.option.usage_ref()

  refs = documented_options.flatmap(lambda opts: chain(*opts)).map(lambda o: OptionRef(o))

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

  sections = recursive(
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

class Options(AstNode):
  def __init__(self, options):
    self.options = options

  def __repr__(self):
    return f"""<Options>
  {self.indent(self.options)}"""

  def __str__(self):
    lines = '\n'.join(map(lambda opt: f'  {opt}', self.options))
    return f"""Options:
{lines}
"""

  sections = documented_options.map(lambda opts: map(Options, opts))

class DocoptAst(AstNode):
  def __init__(self, usage, options):
    self.usage = usage
    self.options = options

  def __repr__(self):
    return f'''<Docopt>
  usage:
{self.indent([self.usage], 2)}
  options:
{self.indent(self.options, 2)}'''

  def __str__(self):
    option_sections = '\n'.join(map(str, self.options))
    return f'''{self.usage}
{option_sections}
'''

  asts = tuples(Usage.sections, Options.sections).map(lambda n: DocoptAst(*n))



if __name__ == "__main__":
  import sys
  sys.ps1 = '>>>'
  print(DocoptAst.asts.example())
