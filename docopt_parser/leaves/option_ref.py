from docopt_parser import base, leaves, marks

class OptionRef(base.AstLeaf):
  ref: leaves.DocumentedOption

  def __init__(self, range: marks.RangeTuple, ref: leaves.DocumentedOption):
    super().__init__(marks.Range(range).wrap_element(ref.ident).to_marked_tuple())
    self.ref = ref

  @property
  def multiple(self) -> bool:
    return self._multiple

  @multiple.setter
  def multiple(self, val: bool):
    self._multiple = val
    self.ref.multiple = val

  def __repr__(self):
    return f'<OptionRef{self.multiple_suffix}> {self.ident}'

  def __iter__(self):
    yield from super().__iter__()
    yield 'ref', self.ref.dict
