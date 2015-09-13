"""py.py
"""

import sys


class Origin(object):

  def __init__(self, filename, string, position):
    self.filename = filename
    self.string = string
    self.position = position

  def LocationMessage(self):
    return 'in %s on line %d column %d\n%s\n%s*\n' % (
        self.filename,
        self.LineNumber(),
        self.ColumnNumber(),
        self.Line(),
        ' ' * (self.ColumnNumber() - 1))

  def LineNumber(self):
    return 1 + self.string.count('\n', 0, self.position)

  def ColumnNumber(self):
    return 1 + self.position - self.LineStart()

  def Line(self):
    return self.string[self.LineStart():self.LineEnd()]

  def LineStart(self):
    return self.string.rfind('\n', 0, self.position) + 1

  def LineEnd(self):
    p = self.string.find('\n', self.position)
    return len(self.string) if p == -1 else p


class Token(object):

  def __init__(self, type, value=None, origin=None):
    self.type = type
    self.value = value
    self.origin = origin

  def __eq__(self, other):
    return self.type == other.type and self.value == other.value

  def __repr__(self):
    return 'Token(%r,%r)' % (self.type, self.value)

SYMBOLS = (
    '\\', '.',
    '(', ')', '[', ']',
    '=',
    ';', ',',
)


KEYWORDS = (
    'while', 'break',
    'if', 'else',
    'and', 'or',
    'return',
    'var',
)


class LexError(Exception):

  def __init__(self, message, origin):
    super(LexError, self).__init__(message + '\n' + origin.LocationMessage())


def Lex(string, filename):
  tokens = []
  depth = 0
  s = string
  i = 0
  indent_stack = ['']

  def MakeOrigin():
    return Origin(filename, s, j)

  def MakeToken(type_, value=None):
    return Token(type_, value, MakeOrigin())

  while True:
    while i < len(s) and ((s[i].isspace() and (depth or s[i] != '\n')) or s[i] == '#'):
      if s[i] == '#':
        while i < len(s) and s[i] != '\n':
          i += 1
      else:
        i += 1

    j = i

    if i >= len(s):
      break
    elif s[i] == '\n':
      i += 1
      tokens.append(MakeToken('Newline'))

      while True:
        j = i
        while i < len(s) and s[i].isspace() and s[i] != '\n':
          i += 1
        if i < len(s) and s[i] == '#':
          while i < len(s) and s[i] != '\n':
            i += 1
        if i >= len(s) or not s[i].isspace():
          break
        i += 1

      if i < len(s):
        indent = s[j:i]
        if indent == indent_stack[-1]:
          pass
        elif indent.startswith(indent_stack[-1]):
          tokens.append(MakeToken('Indent'))
          tokens.append(MakeToken('Newline'))
          indent_stack.append(indent)
        elif indent in indent_stack:
          while indent != indent_stack[-1]:
            tokens.append(MakeToken('Dedent'))
            tokens.append(MakeToken('Newline'))
            indent_stack.pop()
        else:
          raise LexError('Invalid indent: ' + repr(indent), MakeOrigin())

    elif s[i].isdigit() or s[i] == '.' and s[i+1:i+2].isdigit():
      while i < len(s) and s[i].isdigit():
        i += 1
      if i < len(s) and s[i] == '.':
        i += 1
        while i < len(s) and s[i].isdigit():
          i += 1
      tokens.append(MakeToken('Number', eval(s[j:i])))
    elif s.startswith(('r"', "r'", '"', "'"), i):
      raw = False
      if s[i] == 'r':
        i += 1
        raw = True
      quote = s[i:i+3] if s.startswith(('"""', "'''"), i) else s[i:i+1]
      i += len(quote)
      while not s.startswith(quote, i):
        if i >= len(s):
          raise LexError("Missing quotes for: " + quote, MakeOrigin())
        i += 2 if not raw and s[i] == '\\' else 1
      i += len(quote)
      tokens.append(MakeToken('String', eval(s[j:i])))
    elif s[i].isalnum() or s[i] == '_':
      while i < len(s) and (s[i].isalnum() or s[i] == '_'):
        i += 1
      word = s[j:i]
      if word in KEYWORDS:
        tokens.append(MakeToken(word))
      else:
        tokens.append(MakeToken('Name', word))
    elif s.startswith(SYMBOLS, i):
      symbol = max(symbol for symbol in SYMBOLS if s.startswith(symbol, i))
      if symbol in ('(', '{', '['):
        depth += 1
      elif symbol in (')', '}', ']'):
        depth -= 1
      i += len(symbol)
      tokens.append(MakeToken(symbol))
    else:
      while i < len(s) and not s[i].isspace():
        i += 1
      raise LexError("Unrecognized token: " + s[j:i], MakeOrigin())

  while indent_stack[-1] != '':
    tokens.append(MakeToken('Dedent'))
    indent_stack.pop()

  tokens.append(MakeToken('End'))

  return tokens


class Node(object):

  def __init__(self, type, value, children, origin=None):
    self.type = type
    self.value = value
    self.children = children
    self.origin = origin

    if origin is not None and not isinstance(origin, Origin):
      raise TypeError('origin must be None or Origin but found ' + str(type(origin)))

  def __repr__(self):
    return 'Node(%r, %r, %r)' % (self.type, self.value, self.children)

  def __eq__(self, other):
    return (self.type, self.value, self.children) == (other.type, other.value, other.children)


class ParseError(Exception):

  def __init__(self, message, origin):
    super(ParseError, self).__init__(message + '\n' + origin.LocationMessage())


def Parse(string, filename):
  toks = Lex(string, filename)
  i = [0]

  def Peek(lookahead=0):
    return toks[i[0]+lookahead]

  def At(type_, origin=None, lookahead=0):
    if Peek(lookahead).type == type_:
      if origin:
        origin[0] = Peek(lookahead).origin
      return True

  def GetToken():
    tok = toks[i[0]]
    i[0] += 1
    return tok

  def Consume(type_, origin=None):
    if At(type_, origin):
      return GetToken()

  def Expect(type_, origin=None):
    if not At(type_, origin):
      raise ParseError('Expected %s but found %s' % (type_, Peek().type), Peek().origin)
    return GetToken()

  def Any(*parsers):
    for parser in parsers[:-1]:
      try:
        return parser()
      except ParseError:
        pass
    return parsers[-1]()

  def EatExpressionDelimiters():
    while Consume('Newline') or Consume(';'):
      pass

  def Statement():
    return Any(SmallStatement, CompoundStatement)

  def SmallStatement():
    return Any(ExpressionStatement, DelStatement, PassStatement, FlowStatement, ImportStatement, AssertStatement)

  def ExpressionStatement():
    pass

###############################################################################
###############################################################################
###############################################################################
### Test
###############################################################################
###############################################################################
###############################################################################

origin = Origin('<test>', """
hello world!
""", 1)

assert origin.Line() == 'hello world!', repr(origin.Line())

assert origin.LocationMessage() == """in <test> on line 2 column 1
hello world!
*
""", repr(origin.LocationMessage())

tokens = Lex("""
"hello".Print()
""", '<test>')

assert (
    tokens ==
    [
        Token('Newline'),
        Token('String', 'hello'),
        Token('.'),
        Token('Name', 'Print'),
        Token('('),
        Token(')'),
        Token('Newline'),
        Token('End'),
    ]
), tokens

tokens = Lex("""
i = 0
while i.LessThan(10)
  i.Print()
  i = i.Add(1)

""", '<test>')

assert (
    tokens ==
    [
        Token('Newline'),

        Token('Name', 'i'),
        Token('='),
        Token('Number', 0),
        Token('Newline'),

        Token('while'),
        Token('Name', 'i'),
        Token('.'),
        Token('Name', 'LessThan'),
        Token('('),
        Token('Number', 10),
        Token(')'),
        Token('Newline'),

        Token('Indent'),

          Token('Newline'),

          Token('Name', 'i'),
          Token('.'),
          Token('Name', 'Print'),
          Token('('),
          Token(')'),
          Token('Newline'),

          Token('Name', 'i'),
          Token('='),
          Token('Name', 'i'),
          Token('.'),
          Token('Name', 'Add'),
          Token('('),
          Token('Number', 1),
          Token(')'),
          Token('Newline'),

        Token('Dedent'),

        Token('End'),
    ]
), tokens

try:
  Lex('!@#', '<test>')
except LexError as e:
  assert str(e) == """Unrecognized token: !@#
in <test> on line 1 column 1
!@#
*
""", str(e)
else:
  assert False, "Lex('!@#', '<test>') should have raised error but didn't"
