"""ccl.py"""

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
      quote = s[i:i+3] if s.startswith(('""""', "'''"), i) else s[i:i+1]
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
  """
  Parse node types:

    Name
    String
    Number
    List
    Function
    Block
    break
    var
    if
    while
    return
    Call
    Arguments
    GetAttribute
    SetAttribute
    and
    or
    Assign
  """

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

  def EatExpressionDelimiters():
    while Consume('Newline') or Consume(';'):
      pass

  def Expression():
    return AssignExpression()

  def MakeNodeFromToken(token):
    return Node(token.type, token.value, [], token.origin)

  def PrimaryExpression():
    origin = [None]
    if At('Name') or At('String') or At('Number'):
      return MakeNodeFromToken(GetToken())
    elif Consume('[', origin):
      exprs = []
      while not Consume(']'):
        exprs.append(Expression())
        Consume(',')
      return Node('List', None, exprs, origin[0])
    elif Consume('\\', origin):
      args = []
      while At('Name'):
        args.append(GetToken().value)
        Consume(',')
      dot_origin = [None]
      if Consume('.', dot_origin):
        body = Node('return', None, [Expression()], dot_origin[0])
      else:
        EatExpressionDelimiters()
        body = Expression()
      return Node('Function', args, [body], origin[0])
    elif Consume('(', origin):
      expr = Expression()
      Expect(')')
      return expr
    elif Consume('Indent', origin):
      exprs = []
      EatExpressionDelimiters()
      while not Consume('Dedent'):
        exprs.append(Expression())
        EatExpressionDelimiters()
      return Node('Block', None, exprs, origin[0])
    elif Consume('break', origin):
      return Node('break', origin[0])
    elif Consume('var', origin):
      names = []
      values = []
      while At('Name'):
        names.append(GetToken().value)
        if Consume('='):
          values.append(Expression())
        else:
          values.append(Node('Name', 'nil', [], origin[0]))
        Consume(',')
      return Node('var', names, values, origin[0])
    elif Consume('if', origin):
      exprs = [Expression()] # test
      EatExpressionDelimiters()
      exprs.append(Expression()) # body
      EatExpressionDelimiters()
      if Consume('else'):
        EatExpressionDelimiters()
        exprs.append(Expression()) # else
      elif Peek(-1).type in (';', 'Newline'): # TODO: Find more elegant solution.
        i[0] -= 1
      return Node('if', None, exprs, origin[0])
    elif Consume('while', origin):
      exprs = [Expression()] # test
      EatExpressionDelimiters()
      exprs.append(Expression()) # body
      return Node('while', None, exprs, origin[0])
    elif Consume('return', origin):
      return Node('return', None, [Expression()], origin[0])
    raise ParseError('Expected Expression but found %s' % (Peek().type,), Peek().origin)

  def PostfixExpression():
    expr = PrimaryExpression()
    while True:
      if Consume('('):
        args = []
        while not Consume(')'):
          args.append(Expression())
          Consume(',')
        if At('\\'):
          args.append(PrimaryExpression())
        expr = Node('Call', None, [expr, Node('Arguments', None, args, expr.origin)], expr.origin)
      elif Consume('.'):
        name = Expect('Name').value
        if Consume('='):
          expr = Node('SetAttribute', name, [expr, Expression()], expr.origin)
        else:
          expr = Node('GetAttribute', name, [expr], expr.origin)
      else:
        break
    return expr

  def AndExpression():
    expr = PostfixExpression()
    while Consume('and'):
      expr = Node('and', [expr, AndExpression()])
    return expr

  def OrExpression():
    expr = AndExpression()
    while Consume('or'):
      expr = Node('or', [expr, OrExpression()])
    return expr

  def AssignExpression():
    if At('Name') and At('=', None, 1):
      origin = [None]
      name = Expect('Name', origin).value
      Expect('=')
      return Node('Assign', name, [AssignExpression()], origin[0])
    return OrExpression()

  exprs = []
  EatExpressionDelimiters()
  while not At('End'):
    exprs.append(Expression())
    EatExpressionDelimiters()

  return Node('Module', None, exprs, exprs[0].origin if exprs else Expect('End').origin)


class Object(object):

  def XXPrint(self):
    print(self)
    return self

  def XXString(self):
    return String('<Object %d>' % id(self))

  def XXEqual(self, other):
    return Bool(id(self) == id(other))

  def __eq__(self, other):
    return self.XXEqual(other)

  def __bool__(self):
    return self.__nonzero__()

  def __nonzero__(self):
    return self.XXBool().value

  def __str__(self):
    return self.XXString().value

class Nil(Object):

  def XXString(self):
    return String('nil')

  def XXBool(self):
    return false

nil = Nil()


class WrapedObject(Object):

  def __init__(self, value):
    self.value = value

  def XXBool(self):
    return true if self.value else false

  def XXEqual(self, other):
    return type(self) == type(other) and self.value == other.value


class Bool(WrapedObject):

  def __init__(self, value):
    self.value = value

  def XXString(self):
    return String('true' if self.value else 'false')

  def XXBool(self):
    return self

true = Bool(True)
false = Bool(False)


class Number(WrapedObject):

  def __init__(self, value):
    self.value = value

  def XXAdd(self, other):
    if isinstance(other, Number):
      return Number(self.value + other.value)
    raise Exception((other.type, other))

  def XXLessThan(self, other):
    if not isinstance(other, Number):
      raise CclError('Can only Number.LessThan with other numbers')
    return Bool(self.value < other.value)

  def XXString(self):
    return String(str(self.value))


class String(WrapedObject):

  def __init__(self, value):
    self.value = value

  def XXString(self):
    return self


class List(WrapedObject):

  def __init__(self, value):
    self.value = value

  def XXPush(self, other):
    self.value.append(other)

  def XXString(self):
    return String('[%s]' % ', '.join(map(str, self.value)))


class BuiltinFunction(WrapedObject):

  def __call__(self, *args):
    result = self.value(*args)
    return nil if result is None else result


class UserFunction(Object):

  def __init__(self, scope, args, body):
    self.scope = scope
    self.args = args
    self.body = body

  def __call__(self, *args):
    scope = Scope(self.scope)
    for name, arg in zip(self.args, args):
      scope.Declare(name)
      scope[name] = arg
    return Evaluate(scope, self.body)

  def XXBool(self):
    return true


class Scope(object):

  def __init__(self, parent=None):
    self.parent = parent
    self.table = dict()

  def Declare(self, key, value=None):
    self.table[key] = nil if value is None else value

  def DeclareBuiltin(self, f):
    self.table[f.__name__] = BuiltinFunction(f)

  def __getitem__(self, key):
    if key in self.table:
      return self.table[key]
    elif self.parent is not None:
      return self.parent[key]
    else:
      raise KeyError(key)

  def __setitem__(self, key, value):
    assert isinstance(value, Object)
    if key in self.table:
      self.table[key] = value
    elif self.parent is not None:
      self.parent[key] = value
    else:
      raise KeyError(key)

ROOT_SCOPE = Scope()
ROOT_SCOPE.Declare('nil', nil)
ROOT_SCOPE.Declare('true', true)
ROOT_SCOPE.Declare('false', false)


@ROOT_SCOPE.DeclareBuiltin
def Assert(cond, message=''):
  if not cond:
    raise AssertError('Assertion error: ' + str(message))


@ROOT_SCOPE.DeclareBuiltin
def Create():
  return Object()


class CclError(Exception):

  def __init__(self, message):
    super(CclError, self).__init__(message + '\n' + origin.LocationMessage())
    self.message = message
    self.trace = []

  def __str__(self):
    return self.message + '\n' + ''.join(origin.LocationMessage() for origin in self.trace)


class BreakException(Exception):
  pass


class ReturnException(Exception):

  def __init__(self, value):
    self.value = value


class AssertError(CclError):
  pass


def Evaluate(scope, node):

  if not isinstance(node.origin, Origin):
    raise TypeError((node.type, node.origin))

  try:
    if node.type == 'Module':
      last = nil
      for child in node.children:
        last = Evaluate(scope, child)
      return last
    elif node.type == 'Name':
      try:
        return scope[node.value]
      except KeyError as e:
        raise CclError('%s is not defined' % str(e))
    elif node.type == 'String':
      return String(node.value)
    elif node.type == 'Number':
      return Number(node.value)
    elif node.type == 'List':
      return List([Evaluate(scope, n) for n in node.children])
    elif node.type == 'Function':
      return UserFunction(scope, node.value, node.children[0])
    elif node.type == 'Block':
      last = nil
      for child in node.children:
        last = Evaluate(scope, child)
      return last
    elif node.type == 'break':
      raise BreakException()
    elif node.type == 'var':
      for name, arg in zip(node.value, node.children):
        scope.Declare(name)
        scope[name] = Evaluate(scope, arg)
      return nil
    elif node.type == 'if':
      if Evaluate(scope, node.children[0]):
        return Evaluate(scope, node.children[1])
      elif len(node.children) == 2:
        return nil
      else:
        return Evaluate(scope, node.children[2])
    elif node.type == 'while':
      last = nil
      while Evaluate(scope, node.children[0]):
        last = Evaluate(scope, node.children[1])
      return last
    elif node.type == 'return':
      raise ReturnException(Evaluate(scope, node.children[0]))
    elif node.type == 'Call':
      f = Evaluate(scope, node.children[0])
      args = Evaluate(scope, node.children[1])
      try:
        return f(*args)
      except ReturnException as e:
        return e.value
      except CclError as e:
        e.trace.append(node.origin)
        raise
    elif node.type == 'Arguments':
      return [Evaluate(scope, n) for n in node.children]
    elif node.type == 'GetAttribute':
      value, = node.children
      owner = Evaluate(scope, value)
      attr = 'XX' + node.value
      try:
        return getattr(owner, attr)
      except AttributeError:
        raise CclError('Object has no attribute ' + node.value)
    elif node.type == 'SetAttribute':
      lhs, rhs = [Evaluate(scope, n) for n in node.children]
      return setattr(lhs, 'XX' + node.value, rhs)
    elif node.type == 'and':
      lhs, rhs = node.children
      lhs = Evaluate(scope, lhs)
      if lhs:
        return Evaluate(scope, rhs)
      else:
        return lhs
    elif node.type == 'or':
      lhs, rhs = node.children
      lhs = Evaluate(scope, lhs)
      if lhs:
        return lhs
      else:
        return Evaluate(scope, rhs)
    elif node.type == 'Assign':
      name = node.value
      value = Evaluate(scope, node.children[0])
      try:
        scope[name] = value
      except KeyError as e:
        raise CclError('%s is not defined' % str(e))
      return value

    raise CclError('Unrecognized node ' + node.type)
  except CclError as e:
    if not e.trace:
      e.trace.append(node.origin)
    raise


def Run(string, filename=None):
  return Evaluate(ROOT_SCOPE, Parse(string, filename or '<unknown>'))


def RunX(string, filename=None):
  try:
    return Run(string, filename)
  except CclError as e:
    sys.stderr.write('***** Error *****\n' + str(e))
    exit(1)


### Test

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

node = Parse("""
i = 0
while i.LessThan(10)
  i.Print()
  i = i.Add(1)
""", "<test>")

assert node == Node('Module', None, [
    Node('Assign', 'i', [Node('Number', 0, [])]),
    Node('while', None, [
        Node('Call', None, [
            Node('GetAttribute', 'LessThan', [Node('Name', 'i', [])]),
            Node('Arguments', None, [
                Node('Number', 10, []),
            ]),
        ]),
        Node('Block', None, [
            Node('Call', None, [
                Node('GetAttribute', 'Print', [Node('Name', 'i', [])]),
                Node('Arguments', None, []),
            ]),
            Node('Assign', 'i', [
                Node('Call', None, [
                    Node('GetAttribute', 'Add', [Node('Name', 'i', [])]),
                    Node('Arguments', None, [
                        Node('Number', 1, []),
                    ]),
                ]),
            ]),
        ]),
    ]),
]), node

node = Parse("a.b = 4.4", '<test>')

assert node == Node('Module', None, [
    Node('SetAttribute', 'b', [
        Node('Name', 'a', []),
        Node('Number', 4.4, []),
    ]),
]), node

try:
  Parse('=', '<test>')
except ParseError as e:
  assert str(e) == """Expected Expression but found =
in <test> on line 1 column 1
=
*
""", str(e)
else:
  assert False, "Parse('=', '<test>') should have raised error but didn't"

try:
  Run("Assert(false)")
except AssertError as e:
  pass
else:
  assert False, "Assert(false) should have raised error but didn't"

RunX(r"""
Assert("a".Equal("a"), '"a" should equal "a"')
Assert((1).Add(2).Equal(3))

var i xs

xs = []
i = 0
while i.LessThan(3)
  xs.Push(i)
  i = i.Add(1)

Assert(xs.Equal([0, 1, 2]), xs)
Assert(xs.String().Equal('[0, 1, 2]'), xs.String())

""")

### Main

if __name__ == '__main__':
  RunX(sys.stdin.read(), '<stdin>')
