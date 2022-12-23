self.STRING_REGEX_SINGLE = "'[^'\r\n]*'"
# a literal '
# anything which isn't ' or a newline 0 or more times
# a literal '

self.STRING_REGEX_DOUBLE = re.compile('"[^"\r\n]*"')
# a literal ",
# anything which isn't " or a newline 0 or more times
# a literal "

self.NUMBER_REGEX = re.compile(
    \b          # begin with a word boundry (punctuation or space)
    (?=\(*)     # match but don't highlight 0 or more opening brackets
    \d+\.?\d*   # match 1 or more numbers, 0 or 1 decimal points, 0 or more numbers
    (?=\)*\,*)  # match but don't highlight 0 or more closing brackets or commas
    \b          # end with a word boundry (punctuation or space)
)


self.KEYWORDS_REGEX = re.compile(
    (?=\(*)           # match but don't highlight 0 or more opening brackets
    (?<![a-z])        # don't match if it begins with an alphabet character
    (None|True|False) # match None or True or False
    (?=\)*\,*)        # match but don't highlight 0 or more closing brackets or commas
)

self.SELF_REGEX = re.compile(
    (?=\(*)    # same as above
    (?<![a-z]) # same as above
    (self)     # match self
    (?=\)*\,*) # same as above
)


self.FUNCTIONS_REGEX = re.compile(
    (?=\(*)                       # same as above
    (?<![a-z])                    # same as above
    (print|list|dict|set|int|str) # literal match print, list, dict, etc.
    (?=\()                        # match but dont capture 1 opening bracket
)
