from .optionref import OptionRef
from .identnode import IdentNode
from parsec import generate
from .long import inline_long_option_spec
from .short import Short, inline_short_option_spec, shorts_list_inline_short_option_spec

# inline_option_spec: Parses an option that is specified inline in the usage section and adds it to the options list
def inline_option_spec(options, shorts_list):
  @generate('inline option spec')
  def p():
    if shorts_list:
      opt = yield shorts_list_inline_short_option_spec
    else:
      opt = yield (inline_short_option_spec | inline_long_option_spec)
    if isinstance(opt, Short):
      option = Option(opt, None, False, None, None, None)
    else:
      option = Option(None, opt, False, None, None, None)
    ref = OptionRef(option, opt, opt.arg)
    options.add(option)
    return ref
  return p

class Option(IdentNode):

  def __init__(self, short, long, shortcut, doc1, default, doc2):
    super().__init__(long.ident if long else short.ident)
    self.short = short
    self.long = long
    self.shortcut = shortcut
    self.expects_arg = any([o.arg for o in [short, long] if o is not None])
    self.default = default
    self.doc = ''.join(t for t in [
      doc1 or '',
      default or f'[default: {default}]',
      doc2 or '',
    ])

  def __repr__(self):
    return f'''<Option>{self.repeatable_suffix}
  short: {self.indent(self.short) if self.short else 'None'}
  long:  {self.indent(self.long) if self.long else 'None'}
  shortcut: {self.shortcut}
  arg?:     {self.expects_arg}
  default:  {self.default}
  doc:      {self.doc}'''

  # usage_ref: Parse references to this option in the usage section
  # shorts_list=True modifies the parser to parse references from the "-abc" short option list syntax
  @property
  def usage_ref(self):
    return self._usage_ref(shorts_list=False)

  @property
  def shorts_list_usage(self):
    return self._usage_ref(shorts_list=True)

  def _usage_ref(self, shorts_list):
    def to_ref(tup):
      # Once an option has been referenced from the usage section directly
      # it is no longer accessible via the "options" shortcut
      self.shortcut = False
      ref, arg = tup
      return OptionRef(self, ref, arg)
    if self.short is None:
      if shorts_list:
        return None
      return self.long.usage_ref.parsecmap(to_ref)
    if self.long is None or shorts_list:
      return self.short._usage_ref(shorts_list).parsecmap(to_ref)
    return (
      self.short._usage_ref(shorts_list)
      | self.long.usage_ref
    ).parsecmap(to_ref)
