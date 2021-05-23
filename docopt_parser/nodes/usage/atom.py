from parsec import generate

def atom(options):

  @generate('any element (cmd, ARG, options, --option, (group), [optional], --)')
  def p():
    from .group import Group
    from .optional import Optional
    from .optionsshortcut import OptionsShortcut
    from .argumentseparator import ArgumentSeparator
    from .optionlist import OptionList
    from ..argument import Argument
    from .command import Command
    from .multiple import Multiple
    # Instead of doing special handling for OptionList which is the only
    # element that can be a list, we handle everything as a list
    elements = yield (
        Group.group(options) | Optional.optional(options) | OptionsShortcut.shortcut
        | ArgumentSeparator.separator | OptionList.options(options)
        | Argument.arg | Command.command
    ).desc('any element (cmd, ARG, options, --option, (group), [optional], --)')
    if not isinstance(elements, list):
      elements = [elements]
    elements[-1] = yield Multiple.multi(elements[-1])
    return elements
  return p
