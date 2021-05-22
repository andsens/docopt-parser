

def atom(options):
  from .group import Group
  from .optional import Optional
  from .optionsshortcut import OptionsShortcut
  from .argumentseparator import ArgumentSeparator
  from .options import Options
  from ..argument import Argument
  from .command import Command
  from .multiple import Multiple
  return (
    Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
    | ArgumentSeparator.separator | Options.options(options)
    | Argument.arg | Command.command
  ).bind(Multiple.multi).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')
