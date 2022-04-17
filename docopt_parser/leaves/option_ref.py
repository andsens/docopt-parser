from docopt_parser import base, leaves, marks

class OptionRef(base.IdentNode):
  ref: leaves.DocumentedOption

  def __init__(self, range: marks.RangeTuple, ref: leaves.DocumentedOption):
    super().__init__(marks.Range(range).wrap_element(ref.ident).to_marked_tuple())
    self.ref = ref

  def __repr__(self):
    return f'<OptionRef> {self.ident}'

  def __iter__(self):
    yield from super().__iter__()
