#!/usr/bin/env python3

import re
from parsec import Parser, Value, bind, eof, letter, many, none_of, optional, regex, separated, skip, string, try_choice

# '''
# ^(
#   [^\n]*
#   usage:
#   [^\n]*
#   \n?
#   (?:
#     [ \t]
#     .*?
#     (?:\n|$)
#   )*
# )
# '''
# usage_section = many(
#   many(none_of('\n')) >>
#   string('usage:') >>
#   many(none_of('\n')) >>
#   optional(string('\n')) >>
#   choice(string(' '), string('\t')) >>
#   ends_with(
#     none_of(''),
#     choice(string('\n'), eof())
#   )
# )


def this_not_that(p, notthat):
  def parse(text, index):
    res = notthat(text, index)
    if res.status:
      return Value.failure(index, 'did not expect ' + res.value)
    else:
      return p(text, index)
  return Parser(parse)





def this_not_that(p, notthat):
  def parse(text, index):
    res = notthat(text, index)
    if res.status:
      return Value.failure(index, 'did not expect ' + res.value)
    else:
      return p(text, index)
  return Parser(parse)


parser = many(this_not_that(letter(), string('ff')))
res = parser.parse('tesfferg')
print(res)
