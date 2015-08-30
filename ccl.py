"""ccl.py

Right now there is probably an issue with not having TCO.
I'm thinking maybe I could use setTimeout to limit the callstack.
But I'll worry about that later if the growing callstack really becomes a problem.

"""
import sys

SYMBOLS = (
    '\\','.',
    ':',
    '+',
    '(', ')', '[', ']', ',', '=',
    '==', '<', '>', '<=', '>=', '!=',
)

KEYWORDS = (
    'while',
    'if', 'else',
    'and', 'or',
)

NATIVE_PRELUDE = r"""

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

function Or(cc, aa, bb) {
  aa(function(a) {
    if (Truthy(a)) { cc(a); return }
    bb(function(b) { cc(b) })
  })
}

function And(cc, aa, bb) {
  aa(function(a) {
    if (!Truthy(a)) { cc(a); return }
    bb(function(b) { cc(b) })
  })
}

function XXNot(cc, x) {
  cc(!Truthy(x))
}

function XXEqual(cc, a, b) {
  switch(TypeOf(a)) {
  case "none":
  case "bool":
  case "num":
  case "str": cc(a === b); return
  case "list":
    if (TypeOf(b) !== "list") { cc(false); return }
    if (b.length !== a.length) { cc(false); return }
    function loop(i) {
      if (i >= a.length) { cc(true); return }
      XXEqual(function(eq) {
        if (!eq) { cc(false); return }
        loop(i+1)
      }, a[i], b[i])
    }
    loop(0)
    return
  }
  throw "Tried to Equal: " + TypeOf(a) + " and " + TypeOf(b)
}

function XXLessThan(cc, a, b) {
  switch(TypeOf(a)) {
  case "bool":
  case "num":
  case "str": cc(a < b); return
  }
  throw "Tried to LessThan: " + TypeOf(a) + " and " + TypeOf(b)
}

function XXRepr(cc, x) {
  switch(TypeOf(x)) {
  case "num": cc(x.toString()); return
  case "str": cc('"' + x.replace('\n', '\\n').replace('"', '\\"') + '"'); return
  case "list":
    var s = '['
    function loop(i) {
      if (i >= x.length) {
        cc(s+']'); return
      }
      XXRepr(function(val) {
        if (i > 0)
          s += ', '
        s += val
        loop(i+1)
      }, x[i])
    }
    loop(0); return
  }
  throw "Tried to Repr " + TypeOf(x)
}

function XXBool(cc, x) {
  cc(Truthy(x))
}

function XXInt(cc, x) {
  switch(TypeOf(x)) {
  case "none": cc(0); return
  case "bool": cc(x ? 1 : 0); return
  case "num": cc(Math.floor(x)); return
  case "str": cc(parseInt(x)); return
  }
  throw "Tried to Int " + TypeOf(x)
}

function XXFloat(cc, x) {
  switch(TypeOf(x)) {
  case "none": cc(0); return
  case "bool": cc(x ? 1 : 0); return
  case "num": cc(x); return
  case "str": cc(parseFloat(x)); return
  }
  throw "Tried to Float " + TypeOf(x)
}

function XXString(cc, x) {
  switch(TypeOf(x)) {
  case "none": cc("None"); return
  case "bool": cc(x ? "True" : "False"); return
  case "num": cc(x.toString()); return
  case "str": cc(x); return
  case "list": XXRepr(cc, x); return
  }
  throw "Tried to String " + TypeOf(x)
}

function XXPrint(cc, x) {
  var args = [], outerargs = arguments
  function loop(i) {
    if (i >= outerargs.length) { console.log.apply(null, args); cc(); return }
    XXString(function(arg) {
      args.push(arg)
      loop(i+1)
    }, outerargs[i])
  }
  loop(1)
}

function XXAdd(cc, a, b) {
  switch(TypeOf(a)) {
  case "num":
    switch(TypeOf(b)) {
    case "num": cc(a + b); return
    }
  }
  throw "Tried to Add " + TypeOf(a) + " and " + TypeOf(b)
}

function XXSize(cc, xs) {
  switch(TypeOf(xs)) {
  case 'list': cc(xs.length); return
  }
  throw "Tried to Size " + TypeOf(xs)
}

function XXGetItem(cc, xs, i) {
  switch(TypeOf(xs)) {
  case 'list':
    switch(TypeOf(i)) {
    case 'num':
      if (i < 0 || i >= xs.length)
        throw "Tried to GetItem of length " + xs.length + " but index is out of bounds " + i
      cc(xs[i]); return
    }
  }
  throw "Tried to GetItem " + TypeOf(xs) + " and " + TypeOf(i)
}

function XXSetItem(cc, xs, i, value) {
  switch(TypeOf(xs)) {
  case 'list':
    switch(TypeOf(i)) {
    case 'num':
      if (i < 0 || i >= xs.length)
        throw "Tried to SetItem of length " + xs.length + " but index is out of bounds " + i
      xs[i] = value
      cc(value); return
    }
  }
  throw "Tried to SetItem " + TypeOf(xs) + " and " + TypeOf(i) + " and " + TypeOf(value)
}

function XXPush(cc, xs, x) {
  xs.push(x)
  cc()
}

"""


PRELUDE = r"""

LessThanOrEqual = \ left right
  left == right or left < right

GreaterThanOrEqual = \ left right
  Not(left < right)

GreaterThan = \ left right
  Not(left <= right)

Map = \ f args
  newargs = []
  i = 0
  while i < Size(args)
    Push(newargs, f(args[i]))
    i = i + 1
  newargs

Reduce = \ f args
  ret = args[0]
  i = 1
  while i < Size(args)
    ret = f(ret, args[i])
    i = i + 1
  ret

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
          indent_stack.append(indent)
        elif indent in indent_stack:
          while indent != indent_stack[-1]:
            tokens.append(('dedent', None))
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
        tokens.append(('id', s[j:i]))
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
  """

  Resulting ast elements:

    Module
      expressions: [Expression]
      variables: [str]

    Block: Expression
      expressions: [Expression]

    If: Expression
      test: Expression
      body: Expression
      else: Expression

    While: Expression
      test: Expression
      body: Expression

    LookupVariable: Expression
      name: str

    Number: Expression
      value: int|float

    String: Expression
      value: str

    List: Expression
      value: [Expression]

    Function: Expression
      arguments: [str]
      body: Expression
      variables: [str]

    Call: Expression
      function: Expression
      arguments: [Expression]

    Assign: Expression
      target: str
      value: Expression

    And: Expression
      left: Expression
      right: Expression

    Or: Expression
      left: Expression
      right: Expression

  Implicitly assumed builtin functions:

    GetAttribute(Object, String)
    SetAttribute(Object, String, Object)

    Not(Object)
    Equal(Object, Object)
    LessThan(Object, Object)

  """
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
    while Consume('newline'):
      pass

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
      else_ = {'type': 'LookupVariable', 'name': 'None'}
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
      return {'type': 'LookupVariable', 'name': GetToken()[1]}
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
        expr = {'type': 'Call', 'function': expr, 'arguments': args}
      elif Consume('['):
        index = Expression()
        Expect(']')
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GetItem'}, 'arguments': [expr, index]}
      elif Consume('.'):
        attr = Expect('id').value
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GetAttribute'}, 'arguments': [expr, {'type': 'String', 'value': attr}]}
      else:
        break
    return expr

  def AdditiveExpression():
    expr = PostfixExpression()
    while True:
      if Consume('+'):
        rhs = PostfixExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'Add'}, 'arguments': [expr, rhs]}
      else:
        break
    return expr

  def CompareExpression():
    expr = AdditiveExpression()
    while True:
      if Consume('=='):
        rhs = AdditiveExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'Equal'}, 'arguments': [expr, rhs]}
      if Consume('<'):
        rhs = AdditiveExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'LessThan'}, 'arguments': [expr, rhs]}
      if Consume('<='):
        rhs = AdditiveExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'LessThanOrEqual'}, 'arguments': [expr, rhs]}
      if Consume('>'):
        rhs = AdditiveExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GreaterThan'}, 'arguments': [expr, rhs]}
      if Consume('>='):
        rhs = AdditiveExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GreaterThanOrEqual'}, 'arguments': [expr, rhs]}
      else:
        break
    return expr

  def LogicalAndExpression():
    expr = CompareExpression()
    while True:
      if Consume('and'):
        rhs = CompareExpression()
        expr = {'type': 'And', 'left': expr, 'right': rhs}
      else:
        break
    return expr

  def LogicalOrExpression():
    expr = LogicalAndExpression()
    while True:
      if Consume('or'):
        rhs = LogicalAndExpression()
        expr = {'type': 'Or', 'left': expr, 'right': rhs}
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
    elif target['type'] == 'Call' and target['function'] == {'type': 'LookupVariable', 'name': 'GetAttribute'}:
      owner, attrexpr = target['arguments']
      return {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'SetAttribute'}, 'arguments': [owner, attrexpr, value]}
    elif target['type'] == 'Call' and target['function'] == {'type': 'LookupVariable', 'name': 'GetItem'}:
      owner, index = target['arguments']
      return {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'SetItem'}, 'arguments': [owner, index, value]}
    elif target['type'] == 'List':
      valuevar = TemporaryVariableName()
      exprs = [{'type': 'Assign', 'target': valuevar, 'value': value}]
      for i, item in enumerate(target['value']):
        exprs.append(TransformAssign(item, {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GetItem'}, 'arguments': [{'type': 'LookupVariable', 'name': valuevar}, {'type': 'Number', 'value': i}]}))
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

  elif node['type'] in ('String', 'Number', 'List', 'LookupVariable'):
    pass

  else:
    raise SyntaxError('Unrecognized type ' + node['type'])

  return variables


# Translate parsed result into a javascript program in the continuation passing style (cps)
def Translate(node):

  if node['type'] == 'Module':
    decls = ''
    if node['variables']:
      decls = 'var ' + ','.join('XX' + v for v in node['variables'])
    s = 'function(cc){cc()}'
    for expr in node['expressions']:
      s = 'function(cc){(%s)(function(){(%s)(cc)})}' % (s, Translate(expr))
    return NATIVE_PRELUDE + ';%s;(%s)(function(){});\n' % (decls, s)

  elif node['type'] == 'Block':
    s = 'function(cc){cc()}'
    for expr in node['expressions']:
      s = 'function(cc){(%s)(function(){(%s)(cc)})}' % (s, Translate(expr))
    return s

  elif node['type'] == 'Or':
    return 'function(cc){Or(cc,(%s),(%s))}' % tuple(map(Translate, (node['left'], node['right'])))

  elif node['type'] == 'And':
    return 'function(cc){And(cc,(%s),(%s))}' % tuple(map(Translate, (node['left'], node['right'])))

  elif node['type'] == 'If':
    return 'function(cc){(%s)(function(testresult){if(Truthy(testresult)){(%s)(cc)}else{(%s)(cc)}})}' % tuple(map(Translate, (node['test'], node['body'], node['else'])))

  elif node['type'] == 'While':
    return 'function(cc){ function loop(){ ((%s)( function(testresult){if(Truthy(testresult)){(%s)(loop)}else{cc()}} )) }; loop()}' % tuple(map(Translate, (node['test'], node['body'])))

  elif node['type'] == 'Call':
    s = 'f(cc%s)' % ''.join(',arg%d' % n for n in range(len(node['arguments'])))
    for i, arg in reversed(tuple(enumerate(node['arguments']))):
      s = '((%s)(function(arg%d){%s}))' % (Translate(arg), i, s)
    return 'function(cc){(%s)(function (f){%s})}' % (Translate(node['function']), s)

  elif node['type'] == 'Assign':
    return 'function(cc){(%s)(function(value){XX%s=value;cc(value)})}' % (Translate(node['value']), node['target'])

  elif node['type'] == 'LookupVariable':
    return 'function(cc){cc(%s)}' % ('XX' + node['name'])

  elif node['type'] == 'Number':
    return 'function(cc){cc(%s)}' % node['value']

  elif node['type'] == 'String':
    return 'function(cc){cc(%s)}' % '+'.join('String.fromCharCode(%d)' % ord(c) for c in node['value'])

  elif node['type'] == 'List':
    s = 'cc([%s])' % ','.join('arg%d' % n for n in range(len(node['value'])))
    for i, arg in reversed(tuple(enumerate(node['value']))):
      s = '((%s)(function(arg%d){%s}))' % (Translate(arg), i, s)
    return 'function(cc){%s}' % s

  elif node['type'] == 'Function':
    decls = ''
    if node['variables']:
      decls = 'var ' + ','.join('XX' + v for v in node['variables'])
    s = 'function(cc%s){%s;(%s)(cc)}' % (''.join(',XX'+v for v in node['arguments']), decls, Translate(node['body']))
    return 'function(cc){cc(%s)}' % s

  else:
    raise SyntaxError('Unrecognized type ' + node['type'])


if __name__ == '__main__':
  sys.stdout.write(Translate(Parse(PRELUDE + sys.stdin.read())))

