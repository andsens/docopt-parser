from collections import namedtuple

Multiple = namedtuple('Multiple', ['atom'])
Long = namedtuple('Long', ['name', 'arg'])
Short = namedtuple('Short', ['name', 'arg'])
Shorts = namedtuple('Shorts', ['name', 'arg'])
Command = namedtuple('Command', ['name'])
Expression = namedtuple('Expression', ['select'])
Optional = namedtuple('Optional', ['select'])
Argument = namedtuple('Argument', ['name'])
OptionsShortcut = namedtuple('OptionsShortcut', [])
OptionLine = namedtuple('OptionLine', ['ident', 'default'])
OptionLines = namedtuple('OptionLines', 'lines')
DocoptAst = namedtuple('DocoptLang', ['usage', 'options'])
