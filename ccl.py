import collections
import sys

Origin = collections.namedtuple('Origin', 'filename position string')
Token = collections.namedtuple('Token', 'type value origin')
Node = collections.namedtuple('Node', 'type value children origin')

SYMBOLS = (
    '\\', '.', '...',
    ':',
    '+', '-', '*', '%',
    '(', ')', '[', ']', ',', '=',
    '==', '<', '>', '<=', '>=', '!=',
    ';',
)

KEYWORDS = (
    'is',
    'while',
    'if', 'else',
    'return',
)

NATIVE_PRELUDE = r"""'use strict';

Object.prototype.XXString = function() { return this.XXInspect(); }
Object.prototype.XX__Equal__ = function(other) { return this === other }
Object.prototype.XX__Add__ = function(other) { return this + other }
Object.prototype.XX__Subtract__ = function(other) { return this - other }
Object.prototype.XX__Multiply__ = function(other) { return this * other }
Object.prototype.XX__Divide__ = function(other) { return this / other }
Object.prototype.XX__Modulo__ = function(other) { return this % other }
Object.prototype.XXPrint = function() { return console.log(this.XXString()) }

var XXNone = new Object(), XXTrue = true, XXFalse = false
XXNone.XXInspect = function() { return 'None' }
XXNone.XX__Bool__ = function() { return false }

Boolean.prototype.XXInspect = function() { return this ? "True" : "False" }
Boolean.prototype.XX__Bool__ = function() { return this }

Number.prototype.XXInspect = function() { return this.toString() }
Number.prototype.XX__LessThan__ = function(other) { return this < other }
Number.prototype.XX__Bool__ = function() { return this !== 0 }

String.prototype.XXInspect = function() { return '"' + this.replace('"', '\\"') + '"' }
String.prototype.XXString = function() { return this }
String.prototype.XX__Bool__ = function() { return this.length !== 0 }

Array.prototype.XXInspect = function() {
  var s = '['
  for (var i = 0; i < this.length; i++) {
    if (i > 0)
      s += ', '
    s += this[i].XXInspect()
  }
  s += ']'
  return s
}
Array.prototype.XX__Equal__ = function(other) {
  if (this.length !== other.length)
    return false
  for (var i = 0; i < this.length; i++)
    if (this[i] !== other[i])
      return false
  return true
}
Array.prototype.XXMap = function(f) { return this.map(f) }
Array.prototype.XX__Bool__ = function() { return this.length !== 0 }
Array.prototype.XXPush = function(x) { this.push(x); return this }
Array.prototype.XXGet = function(index) {
  if (index < 0)
    index += this.length
  if (index < 0 || index >= this.length)
    throw "Index out of bounds: length == " + this.length + " and index = " + index
  return this[index]
}
Array.prototype.XXSet = function(index, value) {
  if (index < 0)
    index += this.length
  if (index < 0 || index >= this.length)
    throw "Index out of bounds: length == " + this.length + " and index = " + index
  this[index] = value
  return value
}

Function.prototype.XXInspect = function() { return '[Function]' }

var XXAssert = new Object()

XXAssert.XXEqual = function(a, b) {
  if (!a.XX__Equal__(b))
    throw "Expected equal, but weren't: left = " + a.XXInspect() + " right = " + b.XXInspect()
}

"""

PRELUDE = r"""
"""


def Lex(string, filename):
  """Given a string and name of file it was extracted from, returns a list of tokens.

  Args:
    string: string to lex.
    filename: name of file this string is from. This function does not check the validity of this value in any way.
  """
  tokens = []
  depth = 0
  s = string
  i = 0
  indent_stack = ['']

  def MakeToken(type_, value=None):
    return Token(type_, value, Origin(filename, j, s))

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
          raise SyntaxError('Invalid indent: ' + repr(indent))

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
          raise SyntaxError("Missing quotes for: " + quote)
        i += 2 if not raw and s[i] == '\\' else 1
      i += len(quote)
      tokens.append(MakeToken('String', eval(s[j:i])))
    elif s[i].isalnum() or s[i] == '_':
      while i < len(s) and s[i].isalnum() or s[i] == '_':
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
      raise SyntaxError("Unrecognized token: " + s[j:i])

  while indent_stack[-1] != '':
    tokens.append(MakeToken('Dedent'))
    indent_stack.pop()

  tokens.append(MakeToken('End'))

  return tokens


def Parse(string, filename):
  """Given a string and source, generates the CST (Concrete Syntax Tree).

  Arguments are semantically the same as in Lex.

  The difference between a CST and an AST (for CCL at least), is that
  CST directly mirrors the syntax and is directly generated by the parser,
  whereas the AST is generated from processing the CST.

  CST node types:

    Module

    Name
    Number
    String
    List
    Function
    Block
    Attribute
    Call

    if
    while
    return

    Arguments # Only found as first child of Function and second child of Call nodes.

    +.
    -.
    .+.
    .-.
    .*.
    ./.
    .%.
    .or.
    .and.
    .==.
    .<.
    .<=.
    .>.
    .>=.

    .=.   # Assignment
    .+=.
    .-=.
    .*=.
    ./=.
    .%=.
    .++
    .--
    ++.
    --.

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

  def Expect(type_, origin=None, error_message=None, error_origin=None):
    if not At(type_, origin):
      raise SyntaxError('Expected %s but found %s' % (type_, Peek()[0]))
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
      return Node('List', None, exprs, origin)
    elif Consume('\\', origin):
      args = []
      while not At('Newline') and not At('.'):
        args.append(PrimaryExpression())
        Consume(',')
      Consume('.')
      EatExpressionDelimiters()
      body = Expression()
      return Node('Function', None, [Node('Arguments', None, args, origin), body], origin)
    elif Consume('(', origin):
      expr = Expression()
      Expect(')', None, None, origin)
      return expr
    elif Consume('Indent', origin):
      exprs = []
      EatExpressionDelimiters()
      while not Consume('Dedent'):
        exprs.append(Expression())
        EatExpressionDelimiters()
      return Node('Block', None, exprs, origin)
    elif Consume('if', origin):
      exprs = [Expression()] # test
      EatExpressionDelimiters()
      exprs.append(Expression()) # body
      EatExpressionDelimiters()
      if Consume('else'):
        EatExpressionDelimiters()
        exprs.append(Expression()) # else
      return Node('if', None, exprs, origin)
    elif Consume('while', origin):
      exprs = [Expression()] # test
      EatExpressionDelimiters()
      exprs.append(Expression()) # body
      return Node('while', None, exprs, origin)
    elif Consume('return', origin):
      return Node('return', None, [Expression()], origin)
    raise SyntaxError('Expected Expression but found %s' % (Peek(),))

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
        expr = Node('Attribute', Expect('Name').value, [expr], expr.origin)
      else:
        break
    return expr

  def MultiplicativeExpression():
    expr = PostfixExpression()
    while any(At(symbol) for symbol in ('*', '/', '%')):
      return Node('.%s.' % GetToken().type, None, [expr, PostfixExpression()], expr.origin)
    return expr

  def AdditiveExpression():
    expr = MultiplicativeExpression()
    while any(At(symbol) for symbol in ('+', '-')):
      return Node('.%s.' % GetToken().type, None, [expr, MultiplicativeExpression()], expr.origin)
    return expr

  def CompareExpression():
    expr = AdditiveExpression()
    if any(At(symbol) for symbol in ('<', '==')):
      return Node('.%s.' % GetToken().type, None, [expr, AdditiveExpression()], expr.origin)
    return expr

  def AssignExpression():
    expr = CompareExpression()
    if Consume('='):
      return Node('.=.', None, [expr, AssignExpression()], expr.origin)
    return expr

  exprs = []
  EatExpressionDelimiters()
  while not At('End'):
    exprs.append(Expression())
    EatExpressionDelimiters()

  return Node('Module', None, exprs, exprs[0].origin if exprs else Expect('End').origin)

def FindAssigned(node):
  variables = set()
  if node.type in ('Attribute',):
    pass
  elif node.type == 'List':
    for child in node.children:
      variables |= FindAssigned(child)
  elif node.type == 'Name':
    variables.add(node.value)
  else:
    raise TypeError(node.type, node)
  return variables

def FindDeclaredVariables(node):
  variables = set()
  if node.type in ('Name', 'Number', 'String', 'Function'):
    pass
  elif node.type in ('List', 'Call', 'Attribute', 'Arguments', 'Block', 'while', 'if', 'return', '.<.', '.+.'):
    for child in node.children:
      variables |= FindDeclaredVariables(child)
  elif node.type in ('.=.', '.+=.'):
    target, _ = node.children
    return FindAssigned(target)
  else:
    raise TypeError(node.type, node)
  return variables

def GenerateDeclarations(names):
  if names:
    return 'var %s;' % ','.join('XX' + name for name in names)
  return ''

def Translate(node, source=None):
  if isinstance(node, str):
    if source is None:
      raise TypeError('Translate needs source to be set if parsing')
    return Translate(Parse(node, source))

  if node.type == 'Module':
    names = set()
    for child in node.children:
      names |= FindDeclaredVariables(child)
    return NATIVE_PRELUDE + ';' + GenerateDeclarations(names) + ';'.join(map(Translate, node.children))
  elif node.type == 'Name':
    return 'XX' + node.value
  elif node.type == 'Number':
    return str(node.value)
  elif node.type == 'String':
    return '"%s"' % node.value.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('\"', '\\"')
  elif node.type == 'List':
    return '[%s]' % ','.join(map(Translate, node.children))
  elif node.type == 'Function':
    args, body = node.children
    decls = GenerateDeclarations(FindDeclaredVariables(body))
    return '(function(%s){%s%s;return XXNone})' % (','.join(map(Translate, args.children)), decls, Translate(body))
  elif node.type == 'Block':
    return '{' + ';'.join(map(Translate, node.children)) + '}'
  elif node.type == 'Attribute':
    return '((%s).XX%s)' % (Translate(node.children[0]), node.value)
  elif node.type == 'Call':
    f, args = node.children
    return '((%s)(%s))' % (Translate(f), Translate(args))
  elif node.type == 'Arguments':
    return ','.join(map(Translate, node.children))
  elif node.type == 'if':
    if len(node.children) == 3:
      return 'if((%s).XX__Bool__()){%s}else{%s}' % tuple(map(Translate, node.children))
    else:
      return 'if((%s).XX__Bool__()){%s}' % tuple(map(Translate, node.children))
  elif node.type == 'while':
    return 'while((%s).XX__Bool__()){%s}' % tuple(map(Translate, node.children))
  elif node.type == 'return':
    return 'return %s' % tuple(map(Translate, node.children))
  elif node.type == '.+.':
    left, right = map(Translate, node.children)
    return '((%s).XX__Add__(%s))' % (left, right)
  elif node.type == '.==.':
    left, right = map(Translate, node.children)
    return '((%s).XX__Equal__(%s))' % (left, right)
  elif node.type == '.=.':
    left, right = map(Translate, node.children)
    return '((%s)%s(%s))' % (left, node.type[1:-1], right)
  elif node.type == '.<.':
    left, right = map(Translate, node.children)
    return '((%s).XX__LessThan__(%s))' % (left, right)
  raise TypeError('Unrecognized node type %s' % node.type)


if __name__ == '__main__':
  sys.stdout.write(Translate(PRELUDE + sys.stdin.read(), '<stdin>'))
