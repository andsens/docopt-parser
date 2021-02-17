from parsita import TextParsers, rep, reg
from parsita.parsers import OptionalParser, lit
from parsita.util import constant
from collections import namedtuple

Docopt = namedtuple('Docopt', ['usage', 'options'])

r_usage = r'[Uu][Ss][Aa][Gg][Ee]:'
r_options = r'[Oo][Pp][Tt][Ii][Oo][Nn][Ss]:'

class Common(TextParsers, whitespace=None):
  indent = lit("\t") | rep(lit(' '))
  nl = lit("\n")
  nextLine = nl & indent

class Usage(TextParsers, whitespace=None):
  title = reg(r'[Uu][Ss][Aa][Gg][Ee]:') > constant('Usage')
  line = prog
  section = title & OptionalParser(Common.nextLine) & line  << Common.nl

class Options(TextParsers, whitespace=None):
  title = reg(r'[Oo][Pp][Tt][Ii][Oo][Nn][Ss]:') > constant('Options')

class Documentation(TextParsers, whitespace=None):
  text = reg(r'(.|\n)+?(?={r_usage}|{r_options})'.format(r_usage=r_usage, r_options=r_options))

class DocoptLang(TextParsers, whitespace=None):
  # doc = rep(Usage.title | reg(r'(.|\n)'))
  doc = Documentation.text
