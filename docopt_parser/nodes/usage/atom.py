

def atom(options):
  from .group import Group
  from .optional import Optional
  from .optionsshortcut import OptionsShortcut
  from .argumentseparator import ArgumentSeparator
  from .options import Options
  from ..argument import Argument
  from .command import Command
  from .multiple import Multiple
  # Use | instead of ^ for unambiguous atoms where we *know* that
  # a given starting character *must* be this specific atom. This way
  # we can give useful error messages of what was expected
  return (
    Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
    | ArgumentSeparator.separator | Options.options(options)
    | Argument.arg | Command.command
  ).bind(Multiple.multi).desc('atom')
