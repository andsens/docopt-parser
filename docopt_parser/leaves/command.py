from docopt_parser import base, marks, parsers

illegal = parsers.non_symbol_chars

class Command(base.IdentNode):
  def __init__(self, name: marks.MarkedTuple[str]):
    super().__init__(name)

  def __repr__(self):
    return f'''<Command{self.multiple_suffix}>{self.repeatable_suffix}: {self.ident}'''

command = base.ident(illegal, starts_with=parsers.char(illegal=illegal | parsers.char('-'))).mark() \
  .parsecmap(lambda n: Command(n))
