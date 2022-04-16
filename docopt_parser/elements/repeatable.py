from docopt_parser import base, marked, parsers

class Repeatable(base.IdentNode):
  __name: marked.Marked[str]
  multiple: bool = False

  def __init__(self, name: marked.MarkedTuple[str]):
    super().__init__(name[1])
    self.__name = marked.Marked(name)

  @property
  def name(self):
    return self.__name.elm

  @property
  def mark(self) -> marked.Mark:
    return self.__name

  def __repr__(self):
    return f'''<Repeatable{self.multiple_suffix}>{self.repeatable_suffix}: {self.name}'''

  def __iter__(self) -> base.DictGenerator:
    yield 'name', self.name

repeatable = parsers.ellipsis.mark().parsecmap(lambda n: Repeatable(n))
