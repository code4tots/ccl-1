"""ccl.py
"""
import sys

SYMBOLS = (
    '\\','.',
    ':',
    '+', '-', '%',
    '(', ')', '[', ']', ',', '=',
    '==', '<', '>', '<=', '>=', '!=',
    ';',
)

KEYWORDS = (
    'is',
    'while',
    'if', 'else',
    'and', 'or',
)


NATIVE_PRELUDE = r"""'use strict';

function TypeOf(x) {
  var to = typeof x
  switch(to) {
  case "undefined": return "none"
  case "boolean": return "bool"
  case "number": return "num"
  case "string": return "str"
  case "object":
    if (Array.isArray(x))
      return "list"
    if (x.constructor === Map)
      return "dict"
    throw x.constructor
  case "function": return "func"
  default: throw "Urecognized TypeOf: " + to
  }
}
function Truthy(x) {
  switch(TypeOf(x)) {
  case "none": return false
  case "bool": return x
  case "num": return x !== 0
  case "str": return x.length > 0
  case "list": return x.length > 0
  }
  throw "Tried to Truthy: " + TypeOf(x)
}
function XXIs(a, b) { return a === b }
function XXAssert(x, message) { if (!Truthy(x)) throw message }
function XXType(x) {
  switch(TypeOf(x)) {
  case "none": return XXNone
  case "bool": return XXBool
  case "num": return XXFloat
  case "str": return XXString
  case "list": return XXList
  }
  throw "Tried to get Type of: " + TypeOf(x)
}
var XXNone = undefined
function XXError(message) { throw message }
function XXNot(x) { return !Truthy(x) }
function XXEqual(a, b) {
  switch(TypeOf(a)) {
  case "none":
  case "bool":
  case "num":
  case "str": return a === b
  case "list":
    if (TypeOf(b) !== "list") { return false }
    if (b.length !== a.length) { return false }
    for (var i = 0; i < a.length; i++)
      if (!XXEqual(a[i], b[i]))
        return false
    return true
  }
  throw "Tried to Equal: " + TypeOf(a) + " and " + TypeOf(b)
}
function XXLessThan(a, b) {
  switch(TypeOf(a)) {
  case "bool":
  case "num":
  case "str": return a < b
  }
  throw "Tried to LessThan: " + TypeOf(a) + " and " + TypeOf(b)
}
function XXRepr(x) {
  switch(x) {
  case XXInt: return "Int"
  case XXFloat: return "Float"
  case XXString: return "String"
  }
  switch(TypeOf(x)) {
  case "num": return x.toString()
  case "str": return '"' + x.replace('\n', '\\n').replace('"', '\\"') + '"'
  case "list":
    var s = '['
    for (var i = 0; i < x.length; i++) {
      if (i > 0)
        s += ', '
      s += XXRepr(x[i])
    }
    s += ']'
    return s
  }
  throw "Tried to Repr " + TypeOf(x)
}
function XXBool(x) {
  return Truthy(x)
}
function XXInt(x) {
  switch(TypeOf(x)) {
  case "none": return 0
  case "bool": return x ? 1 : 0
  case "num": return Math.floor(x)
  case "str": return parseInt(x)
  }
  throw "Tried to Int " + TypeOf(x)
}
function XXFloat(x) {
  switch(TypeOf(x)) {
  case "none": return 0
  case "bool": return x ? 1 : 0
  case "num": return x
  case "str": return parseFloat(x)
  }
  throw "Tried to Float " + TypeOf(x)
}
function XXString(x) {
  switch(TypeOf(x)) {
  case "none": return "None"
  case "bool": return x ? "True" : "False"
  case "num": return x.toString()
  case "str": return x
  default: return XXRepr(x)
  }
  throw "Tried to String " + TypeOf(x)
}
function XXRead() {
  // TODO: Find more portable but still synchronous solution.
  return require('fs').readFileSync('/dev/stdin').toString()
}
function XXPrint(x) {
  XXPrints([x])
  return x
}
function XXPrints(xs) {
  console.log.apply(null, xs.map(XXString))
}
function XXNegate(x) {
  switch(TypeOf(x)) {
  case 'num': return -x
  }
  throw "Tried to Negate " + TypeOf(x)
}
function XXAdd(a, b) {
  switch(TypeOf(a)) {
  case "num":
    switch(TypeOf(b)) {
    case "num": return a + b
    }
  case "str":
    switch(TypeOf(b)) {
    case "str": return a + b
    }
  }
  throw "Tried to Add " + TypeOf(a) + " and " + TypeOf(b)
}
function XXSubtract(a, b) {
  switch(TypeOf(a)) {
  case "num":
    switch(TypeOf(b)) {
    case "num": return a - b
    }
  }
  throw "Tried to Subtract " + TypeOf(a) + " and " + TypeOf(b)
}
function XXModulo(a, b) {
  switch(TypeOf(a)) {
  case "num":
    switch(TypeOf(b)) {
    case "num": return a % b
    }
  }
  throw "Tried to Modulo " + TypeOf(a) + " and " + TypeOf(b)
}
function XXMultiply(a, b) {
  switch(TypeOf(a)) {
  case "num":
    switch(TypeOf(b)) {
    case "num": return a * b
    }
  }
  throw "Tried to Multiply " + TypeOf(a) + " and " + TypeOf(b)
}
function XXSize(xs) {
  switch(TypeOf(xs)) {
  case 'str': return xs.length
  case 'list': return xs.length
  }
  throw "Tried to Size " + TypeOf(xs)
}
function XXGetItem(xs, i) {
  switch(TypeOf(xs)) {
  case 'str':
    switch(TypeOf(i)) {
    case 'num':
      if (i < 0 || i >= xs.length)
        throw "Tried to GetItem of length " + xs.length + " but index is out of bounds " + i
      return xs[i]
    }
  case 'list':
    switch(TypeOf(i)) {
    case 'num':
      if (i < 0 || i >= xs.length)
        throw "Tried to GetItem of length " + xs.length + " but index is out of bounds " + i
      return xs[i]
    }
  }
  throw "Tried to GetItem " + TypeOf(xs) + " and " + TypeOf(i)
}
function XXSetItem(xs, i, value) {
  switch(TypeOf(xs)) {
  case 'list':
    switch(TypeOf(i)) {
    case 'num':
      if (i < 0 || i >= xs.length)
        throw "Tried to SetItem of length " + xs.length + " but index is out of bounds " + i
      return xs[i] = value
    }
  }
  throw "Tried to SetItem " + TypeOf(xs) + " and " + TypeOf(i) + " and " + TypeOf(value)
}
function XXPush(xs, x) {
  xs.push(x)
}
function XXStrip(str) {
  switch(TypeOf(str)) {
  case 'str': return str.replace(/^\s+|\s+$/g, '')
  }
  throw "Tried to Strip " + TypeOf(x)
}
function XXSlice(args, lower, upper, step) {
  if (lower === undefined) lower = 0
  if (upper === undefined) upper = args.length
  if (step === undefined) step = 1
  if (lower < 0)
    lower += args.length
  if (upper <= 0)
    upper += args.length
  if (step !== 1)
    throw "Non-unit step slicing not yet supported: " + step
  return args.slice(lower, upper)
}
function XXSplit(s) {
  return s.split(/\s+/).filter(function(x) { return x !== '' })
}
function XXSplitLines(s) {
  return s.split(/\n+/).filter(function(x) { return x !== '' })
}

;"""


PRELUDE = r"""

###########
## Builtins
###########

Or = \ left rightthunk
  if left
    left
  else
    rightthunk()

And = \ left rightthunk
  if Not(left)
    left
  else
    rightthunk()

LessThanOrEqual = \ left right
  left == right or left < right

GreaterThanOrEqual = \ left right
  Not(left < right)

GreaterThan = \ left right
  Not(left <= right)

For = \ args f
  i = 0
  while i < Size(args)
    f(args[i])
    i = i + 1

Map = \ f args
  newargs = []
  i = 0
  while i < Size(args)
    Push(newargs, f(args[i]))
    i = i + 1
  newargs

FoldLeft = \ f init args
  i = 0
  while i < Size(args)
    init = f(init, args[i])
    i = i + 1
  init

# Fold implies operation is associative and potentially allows for parallel computing.

Fold = FoldLeft

Reduce = \ f args
  if Size(args) < 1
    Error("Reduce's second argument must be a non-empty list, but found an empty one")
  Fold(f, args[0], args[1:])

###################
## End of builtins.
###################

"""


def Lex(s):
  tokens = []
  depth = 0
  i = 0
  indent_stack = ['']

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
      tokens.append(('newline', None))

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
          tokens.append(('indent', None))
          tokens.append(('newline', None))
          indent_stack.append(indent)
        elif indent in indent_stack:
          while indent != indent_stack[-1]:
            tokens.append(('dedent', None))
            tokens.append(('newline', None))
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
      tokens.append(('num', eval(s[j:i])))
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
      tokens.append(('str', eval(s[j:i])))
    elif s[i].isalnum() or s[i] == '_':
      while i < len(s) and s[i].isalnum() or s[i] == '_':
        i += 1
      word = s[j:i]
      if word in KEYWORDS:
        tokens.append((word, None))
      else:
        tokens.append(('id', word))
    elif s.startswith(SYMBOLS, i):
      symbol = max(symbol for symbol in SYMBOLS if s.startswith(symbol, i))
      if symbol in ('(', '{', '['):
        depth += 1
      elif symbol in (')', '}', ']'):
        depth -= 1
      i += len(symbol)
      tokens.append((symbol, None))
    else:
      while i < len(s) and not s[i].isspace():
        i += 1
      raise SyntaxError("Unrecognized token: " + s[j:i])

  while indent_stack[-1] != '':
    tokens.append(('dedent', None))
    indent_stack.pop()

  return tokens


def Parse(s):
  toks = Lex(s)
  i = [0]

  def Peek(lookahead=0):
    return toks[i[0]+lookahead] if i[0]+lookahead < len(toks) else (None, None)

  def At(type_, lookahead=0):
    return Peek(lookahead)[0] == type_

  def GetToken():
    tok = toks[i[0]]
    i[0] += 1
    return tok

  def Consume(type_):
    if At(type_):
      return GetToken()

  def Expect(type_):
    if not At(type_):
      raise SyntaxError('Expected %s but found %s' % (type_, Peek()[0]))
    return GetToken()

  def EatExpressionDelimiters():
    while Consume('newline') or Consume(';'):
      pass

  def Name(name):
    return {'type': 'LookupVariable', 'name': name}

  def Call(f, args):
    return {'type': 'Call', 'function': f, 'arguments': args}

  def Expression():
    return AssignExpression()

  def PrimaryExpression():
    if Consume('('):
      expr = Expression()
      Expect(')')
      return expr
    elif Consume('['):
      exprs = []
      while not Consume(']'):
        exprs.append(Expression())
        Consume(',')
      return {'type': 'List', 'value': exprs}
    elif Consume('indent'):
      exprs = []
      while True:
        EatExpressionDelimiters()
        if Consume('dedent'):
          break
        exprs.append(Expression())
      return {'type': 'Block', 'expressions': exprs}
    elif Consume('if'):
      test = Expression()
      EatExpressionDelimiters()
      body = Expression()
      EatExpressionDelimiters()
      else_ = Name('None')
      if Consume('else'):
        EatExpressionDelimiters()
        else_ = Expression()
      return {'type': 'If', 'test': test, 'body': body, 'else': else_}
    elif Consume('while'):
      test = Expression()
      EatExpressionDelimiters()
      body = Expression()
      return {'type': 'While', 'test': test, 'body': body}
    elif At('id'):
      return Name(GetToken()[1])
    elif At('num'):
      return {'type': 'Number', 'value': GetToken()[1]}
    elif At('str'):
      return {'type': 'String', 'value': GetToken()[1]}
    elif Consume('\\'):
      args = []
      while At('id'):
        args.append(GetToken()[1])
      Consume('.')
      EatExpressionDelimiters()
      body = Expression()
      return {'type': 'Function', 'arguments': args, 'body': body}
    else:
      raise SyntaxError('Expected expression but found %s' % Peek()[0])

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
        expr = Call(expr, args)
      elif Consume('['):
        index = Name('None')
        if not At(':'):
          index = Expression()

        if Consume(']'):
          expr = Call(Name('GetItem'), [expr, index])
        else:
          Expect(':')

          upper = Name('None')
          if not At(':') and not At(']'):
            upper = Expression()

          step = Name('None')
          if Consume(':'):
            if not At(']'):
              step = Expression()

          Expect(']')
          expr = Call(Name('Slice'), [expr, index, upper, step])
      elif Consume('.'):
        attr = Expect('id').value
        expr = Call(Name('GetAttribute'), [expr, {'type': 'String', 'value': attr}])
      else:
        break
    return expr

  def PrefixExpression():
    if Consume('-'):
      return Call(Name('Negate'), [PrefixExpression()])
    return PostfixExpression()

  def MultiplicativeExpression():
    expr = PrefixExpression()
    while True:
      if Consume('%'):
        rhs = PrefixExpression()
        expr = Call(Name('Modulo'), [expr, rhs])
      else:
        break
    return expr

  def AdditiveExpression():
    expr = MultiplicativeExpression()
    while True:
      if Consume('+'):
        rhs = MultiplicativeExpression()
        expr = Call(Name('Add'), [expr, rhs])
      else:
        break
    return expr

  def CompareExpression():
    expr = AdditiveExpression()
    while True:
      if Consume('is'):
        rhs = AdditiveExpression()
        expr = Call(Name('Is'), [expr, rhs])
      elif Consume('=='):
        rhs = AdditiveExpression()
        expr = Call(Name('Equal'), [expr, rhs])
      elif Consume('<'):
        rhs = AdditiveExpression()
        expr = Call(Name('LessThan'), [expr, rhs])
      elif Consume('<='):
        rhs = AdditiveExpression()
        expr = Call(Name('LessThanOrEqual'), [expr, rhs])
      elif Consume('>'):
        rhs = AdditiveExpression()
        expr = Call(Name('GreaterThan'), [expr, rhs])
      elif Consume('>='):
        rhs = AdditiveExpression()
        expr = Call(Name('GreaterThanOrEqual'), [expr, rhs])
      else:
        break
    return expr

  def Suspend(expr):
    return {'type': 'Function', 'arguments': [], 'body': expr}

  def LogicalAndExpression():
    expr = CompareExpression()
    while True:
      if Consume('and'):
        rhs = CompareExpression()
        expr = Call(Name('And'), [expr, Suspend(rhs)])
      else:
        break
    return expr

  def LogicalOrExpression():
    expr = LogicalAndExpression()
    while True:
      if Consume('or'):
        rhs = LogicalAndExpression()
        expr = Call(Name('Or'), [expr, Suspend(rhs)])
      else:
        break
    return expr

  def TemporaryVariableName():
    TemporaryVariableName.counter += 1
    return '__tmp%d' % TemporaryVariableName.counter

  TemporaryVariableName.counter = 0

  def TransformAssign(target, value):
    if target['type'] == 'LookupVariable':
      return {'type': 'Assign', 'target': target['name'], 'value': value}
    elif target['type'] == 'Call' and target['function'] == Name('GetAttribute'):
      owner, attrexpr = target['arguments']
      return Call(Name('SetAttribute'), [owner, attrexpr, value])
    elif target['type'] == 'Call' and target['function'] == Name('GetItem'):
      owner, index = target['arguments']
      return Call(Name('SetItem'), [owner, index, value])
    elif target['type'] == 'List':
      valuevar = TemporaryVariableName()
      exprs = [{'type': 'Assign', 'target': valuevar, 'value': value}]
      for i, item in enumerate(target['value']):
        exprs.append(TransformAssign(item, Call(Name('GetItem'), [Name(valuevar), {'type': 'Number', 'value': i}])))
      return {'type': 'Block', 'expressions': exprs}
    else:
      raise SyntaxError('%s is not assignable' % target['type'])

  def AssignExpression():
    expr = LogicalOrExpression()
    while True:
      if Consume('='):
        expr = TransformAssign(expr, AssignExpression())
      else:
        break
    return expr

  exprs = []
  while True:
    EatExpressionDelimiters()
    if At(None):
      break
    exprs.append(Expression())

  module = {'type': 'Module', 'expressions': exprs}
  AnnotateParseResultsWithVariableDeclarations(module)
  return module


def AnnotateParseResultsWithVariableDeclarations(node):
  variables = set()

  if node['type'] == 'Module':
    node['variables'] = set()
    for expr in node['expressions']:
      node['variables'] |= AnnotateParseResultsWithVariableDeclarations(expr)

  elif node['type'] == 'Block':
    variables = set()
    for expr in node['expressions']:
      variables |= AnnotateParseResultsWithVariableDeclarations(expr)

  elif node['type'] == 'Function':
    node['variables'] = AnnotateParseResultsWithVariableDeclarations(node['body'])
    for arg in node['arguments']:
      node['variables'].discard(arg)

  elif node['type'] == 'Call':
    variables |= AnnotateParseResultsWithVariableDeclarations(node['function'])
    for arg in node['arguments']:
      variables |= AnnotateParseResultsWithVariableDeclarations(arg)

  elif node['type'] in ('Or', 'And'):
    variables |= AnnotateParseResultsWithVariableDeclarations(node['left'])
    variables |= AnnotateParseResultsWithVariableDeclarations(node['right'])

  elif node['type'] == 'If':
    variables |= AnnotateParseResultsWithVariableDeclarations(node['test'])
    variables |= AnnotateParseResultsWithVariableDeclarations(node['body'])
    variables |= AnnotateParseResultsWithVariableDeclarations(node['else'])

  elif node['type'] == 'While':
    variables |= AnnotateParseResultsWithVariableDeclarations(node['test'])
    variables |= AnnotateParseResultsWithVariableDeclarations(node['body'])

  elif node['type'] == 'Assign':
    variables.add(node['target'])
    variables |= AnnotateParseResultsWithVariableDeclarations(node['value'])

  elif node['type'] == 'List':
    for expr in node['value']:
      variables |= AnnotateParseResultsWithVariableDeclarations(expr)

  elif node['type'] in ('String', 'Number', 'LookupVariable'):
    pass

  else:
    raise SyntaxError('Unrecognized type ' + node['type'])

  return variables


def SanitizeStringForJavascript(s):
  return '+'.join('String.fromCharCode(%d)' % ord(c) for c in s)


def Translate(source):

  def Name(name):
    return 'XX' + name

  def Declare(names):
    return 'var %s;' % ','.join(map(Name, names)) if names else ''

  def Block(exprs):
    return '((function(){%s;return %s})())' % (';'.join(map(TranslateNode, exprs[:-1])), TranslateNode(exprs[-1])) if exprs else 'undefined'

  def TranslateNode(node):
    if node['type'] == 'Module':
      return NATIVE_PRELUDE + Declare(node['variables']) + Block(node['expressions'])

    elif node['type'] == 'Block':
      return Block(node['expressions'])

    elif node['type'] == 'If':
      return '(Truthy(%s))?(%s):(%s)' % (TranslateNode(node['test']), TranslateNode(node['body']), TranslateNode(node['else']))

    elif node['type'] == 'While':
      return '(function(){var last;while(Truthy(%s)){last=%s;}return last;})()' % (TranslateNode(node['test']), TranslateNode(node['body']))

    elif node['type'] == 'LookupVariable':
      return Name(node['name'])

    elif node['type'] == 'Number':
      return str(node['value'])

    elif node['type'] == 'String':
      return SanitizeStringForJavascript(node['value'])

    elif node['type'] == 'List':
      return '[%s]' % ','.join(map(TranslateNode, node['value']))

    elif node['type'] == 'Function':
      return 'function(%s){%sreturn %s}' % (','.join(map(Name, node['arguments'])), Declare(node['variables']), TranslateNode(node['body']))

    elif node['type'] == 'Call':
      return '((%s)(%s))' % (TranslateNode(node['function']), ','.join(map(TranslateNode, node['arguments'])))

    elif node['type'] == 'Assign':
      return '(%s=%s)' % (Name(node['target']), TranslateNode(node['value']))

    raise SyntaxError('Unrecognized type ' + node['type'])

  return '// Autogenerated CCL code\n// https://github.com/math4tots/ccl\n// ' + SanitizeStringForJavascript(source) + '\n' + TranslateNode(Parse(source)) + '\n'


if __name__ == '__main__':
  sys.stdout.write(Translate(PRELUDE + sys.stdin.read()))
