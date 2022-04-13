from docopt_parser import groups, parsers

group = (parsers.char('(') >> groups.choice << parsers.char(')')).desc('group')
