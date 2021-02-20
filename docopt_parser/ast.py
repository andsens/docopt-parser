from collections import namedtuple

Multiple = namedtuple('Multiple', ['atom'])
Long = namedtuple('Long', ['name', 'arg'])
Short = namedtuple('Short', ['name', 'arg'])
Shorts = namedtuple('Shorts', ['names', 'arg'])
Command = namedtuple('Command', ['name'])
Choice = namedtuple('Choice', ['items'])
Sequence = namedtuple('Sequence', ['items'])
Optional = namedtuple('Optional', ['item'])
Argument = namedtuple('Argument', ['name'])
OptionsShortcut = namedtuple('OptionsShortcut', [])
OptionLine = namedtuple('OptionLine', ['opts', 'doc1', 'default', 'doc2'])
DocoptAst = namedtuple('DocoptLang', ['usage', 'options'])

Option = namedtuple('Option', ['opts', 'expects_arg', 'default', 'doc'])
OptionRef = namedtuple('OptionRef', ['ref', 'arg'])
