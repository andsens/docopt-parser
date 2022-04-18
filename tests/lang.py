import typing as T
import hypothesis.strategies as HS
from tests import chars, idents, maybe, not_re
from hypothesis.strategies import one_of, just, text, from_regex, tuples, none, lists, integers, shared, booleans, \
  fixed_dictionaries, recursive, sampled_from, permutations
from hypothesis import settings, Verbosity
from functools import reduce
from itertools import chain
import re

settings(verbosity=Verbosity.verbose)

def maybe_s(gen):
  return maybe(gen).flatmap(lambda res: just('') if res is None else just(res))

re_usage = re.compile(r'usage:', re.I)
re_options = re.compile(r'options:', re.I)
re_default = re.compile(r'\[default: [^\]]*\]', re.I)

other_text = text().filter(not_re(re_usage, re_options))
usage_title = from_regex(re_usage, fullmatch=True)
non_symbol_chars = '=|()[], \t\n\r\b\f\x1B\x07\0'

short_idents = chars(illegal=f"{non_symbol_chars}-")
long_idents = idents(illegal=non_symbol_chars, starts_with=chars(illegal=f"{non_symbol_chars}-"))

def partition_options(sizes):
  known_shorts = []
  unused_shorts = short_idents.filter(lambda s: s not in known_shorts)
  known_longs = []
  unused_longs = long_idents.filter(lambda s: s not in known_longs)

  def register_drawn(o: T.Tuple[str, str, bool]):
    short, long, _ = o
    if short:
      known_shorts.append(short)
    if long:
      known_longs.append(long)
    return just(o)

  usage = one_of(
    tuples(unused_shorts, none(), booleans()),
    tuples(none(), unused_longs, booleans()),
  ).flatmap(register_drawn).map(lambda o: UsageOption(*o))

  documented = one_of(
    tuples(unused_shorts, none(), booleans()),
    tuples(none(), unused_longs, booleans()),
    tuples(unused_shorts, unused_longs, booleans()),
  ).flatmap(register_drawn).map(lambda o: DocumentedOption(*o))

  usage_size, *options_sizes = sizes
  return fixed_dictionaries({
    'usage': lists(usage, min_size=usage_size, max_size=usage_size),
    'documented': tuples(*map(
      lambda size: lists(documented, min_size=size, max_size=size),
      options_sizes
    ))
  })

section_sizes: HS.SearchStrategy[T.List[int]] = lists(
  integers(min_value=0, max_value=20), min_size=1, unique=True
).map(lambda indices: reduce(lambda sizes, i: sizes + [i - sum(sizes)], sorted(indices), []))

partitioned_options = shared(section_sizes.flatmap(partition_options))


class AstNode(object):
  def indent(self, node: "AstNode", lvl: int = 1):
    if isinstance(node, T.Iterable):
      lines = '\n'.join(map(repr, node)).split('\n')
      return '\n'.join(['  ' * lvl + line for line in lines])
    else:
      lines = repr(node).split('\n')
      lines = [lines[0]] + ['  ' * lvl + line for line in lines[1:]]
      return '\n'.join(lines)

class IdentNode(AstNode):

  def __init__(self, ident: str):
    super().__init__()
    self.ident = ident

  def __hash__(self):
    return hash(self.ident)

class Option(IdentNode):
  def __init__(self, short: str, long: str, has_arg: bool):
    super().__init__(f'--{long}' if long else f'-{short}')
    self.short = short
    self.long = long
    self.has_arg = has_arg

class DocumentedOption(Option):
  def __repr__(self):
    arg = ' <ARG>' if self.has_arg else ''
    short = f'-{self.short}' if self.short else ''
    long = f'--{self.long}' if self.long else ''
    idents = f'{short}, {long}' if self.short and self.long else short or long
    return f'<Option>: {idents}{arg}'

  def __str__(self):
    arg = ' <ARG>' if self.has_arg else ''
    short = f'-{self.short}' if self.short else ''
    long = f'--{self.long}' if self.long else ''
    idents = f'{short}, {long}' if self.short and self.long else short or long
    return f'{idents}{arg}'

  all = partitioned_options.flatmap(lambda p: just(p['documented']))

class UsageOption(Option):
  def __repr__(self):
    arg = ' <ARG>' if self.has_arg else ''
    return f'<Option>: {self.ident}{arg}'

  def __str__(self):
    arg = ' <ARG>' if self.has_arg else ''
    return f'{self.ident}{arg}'

  all = partitioned_options.flatmap(lambda p: just(p['usage']))
  options = all.flatmap(sampled_from)

class OptionRef(Option):
  def __init__(self, option: Option):
    super().__init__(option.short, option.long, option.has_arg)
    self.option = option

  def __repr__(self):
    return f'''<OptionRef>
  {self.indent(self.option)}'''

  def __str__(self):
    arg = ' <ARG>' if self.has_arg else ''
    ident = f'-{self.short}' if self.short else f'--{self.long}'
    return f'{ident}{arg}'

  all = DocumentedOption.all.map(lambda opts: list(map(OptionRef, chain(*opts))))
  refs = all.flatmap(sampled_from)

class OptionSequence(AstNode):

  def __init__(self, argless_shorts: T.List[Option], short_with_arg: Option):
    super().__init__()
    self.argless_shorts = argless_shorts
    self.short_with_arg = short_with_arg

  def __repr__(self):
    shorts = self.argless_shorts
    if self.short_with_arg:
      shorts.append(self.short_with_arg)
    return f'''<OptionSequence>
{self.indent(shorts)}'''

  def __str__(self):
    argless_shorts = ''.join(map(lambda o: o.short, self.argless_shorts))
    short_with_arg = f'{self.short_with_arg.short} <ARG>' if self.short_with_arg else ''
    return f'-{argless_shorts}{short_with_arg}'

  def flatten_partitioned(partitioned_options):
    return reduce(lambda mem, ls: mem + ls, partitioned_options['documented'], partitioned_options['usage'])

  def sequence_possible(partitioned_options):
    all_options = OptionSequence.flatten_partitioned(partitioned_options)
    argless_count = OptionSequence.count_argless_shorts(all_options)
    with_arg_count = OptionSequence.count_shorts_with_arg(all_options)
    return argless_count >= 2 or (argless_count >= 1 and with_arg_count > 0)

  def count_argless_shorts(all_options):
    return len(list(filter(lambda o: o.short is not None and not o.has_arg, all_options)))

  def count_shorts_with_arg(all_options):
    return len(list(filter(lambda o: o.short is not None and o.has_arg, all_options)))

  all_options = partitioned_options.map(lambda opts: OptionSequence.flatten_partitioned(opts))
  all_shorts = all_options.map(lambda opts: list(filter(lambda o: o.short is not None, opts)))
  all_argless_shorts = all_shorts.map(lambda opts: list(filter(lambda o: not o.has_arg, opts)))
  all_shorts_with_arg = all_shorts.map(lambda opts: list(filter(lambda o: o.has_arg, opts)))

  sequences: HS.SearchStrategy["OptionSequence"] = all_options.flatmap(
    lambda opts: tuples(
      lists(OptionSequence.all_argless_shorts.flatmap(sampled_from), min_size=1, unique=True),
      one_of(none(), OptionSequence.all_shorts_with_arg.flatmap(sampled_from))
    )
    if OptionSequence.count_shorts_with_arg(opts) > 0 else
    tuples(
      lists(OptionSequence.all_argless_shorts.flatmap(sampled_from), min_size=1, unique=True),
      none()
    )
  ).map(lambda o: OptionSequence(*o))

class Command(IdentNode):
  def __repr__(self):
    return f'<Command>: {self.ident}'

  def __str__(self):
    return f"{self.ident}"

  commands = idents(non_symbol_chars, starts_with=chars(illegal=f'{non_symbol_chars}-<')).filter(
    lambda s: not s.isupper()
  ).map(lambda c: Command(c))

class Argument(IdentNode):
  def __repr__(self):
    return f'<Argument>: {self.ident}'

  def __str__(self):
    return self.ident

  wrapped_args = idents(f'{non_symbol_chars}>').map(lambda s: f'<{s}>')
  uppercase_args = idents(non_symbol_chars).filter(lambda s: s.isupper())
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
  def __init__(self, items: T.List[AstNode]):
    super().__init__()
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
  def __init__(self, items: T.List[AstNode]):
    super().__init__()
    self.items = items

  def __repr__(self):
    return f"""<Sequence>
{self.indent(self.items)}"""

  def __str__(self):
    return ' '.join(map(str, self.items))

class Optional(AstNode):
  def __init__(self, items: T.List[AstNode]):
    super().__init__()
    self.items = items

  def __repr__(self):
    return f"""<Optional>
  {self.indent(self.items)}"""

  def __str__(self):
    return f"[{' '.join(map(str, self.items))}]"

class OptionSection(AstNode):
  def __init__(self, options: T.List[Option]):
    super().__init__()
    self.options = options

  def __repr__(self):
    return f"""<Options>
{self.indent(self.options)}"""

  def __str__(self):
    lines = '\n'.join(map(lambda opt: f'  {opt}', self.options))
    return f"""Options:
{lines}
"""

  sections = DocumentedOption.all.map(lambda sections: list(map(OptionSection, sections)))

class UsageSection(AstNode):
  def __init__(self, root: AstNode):
    super().__init__()
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

  def legal_atoms(options):
    legal = [
      ArgumentSeparator.separators,
      Command.commands,
      Argument.args,
      OptionsShortcut.shortcuts,
    ]
    # TODO: Prevent multi...
    if len(options['usage']) > 0:
      legal.append(UsageOption.options)
    if len(options['documented']) > 0:
      legal.append(OptionRef.refs)
    if OptionSequence.sequence_possible(options):
      legal.append(OptionSequence.sequences)
    return one_of(*legal)

  sections = recursive(
    lists(partitioned_options.flatmap(legal_atoms), min_size=1),
    lambda items: one_of(
      just(Choice),
      just(Sequence),
      just(Optional),
    ).flatmap(lambda N: items.map(lambda i: N(i) if type(i) is list else N([i])))
  ).map(lambda n: UsageSection(n))

class DocoptAst(AstNode):
  def __init__(self, sections):
    self.sections = sections

  def __repr__(self):
    return f'''<Docopt>
{self.indent(self.sections, 2)}
"{str(self)}"'''

  def __str__(self):
    return "\n".join(map(str, self.sections))

  def permuted_sections(sections):
    usage, options = sections
    return permutations([usage] + options)

  asts = tuples(UsageSection.sections, OptionSection.sections).flatmap(
    lambda s: DocoptAst.permuted_sections(s)
  ).map(lambda n: DocoptAst(n))


if __name__ == "__main__":
  import sys
  sys.ps1 = '>>>'
  ast = DocoptAst.asts.example()
  print(repr(ast))
