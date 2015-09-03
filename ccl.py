"""ccl.py
"""
import sys

SYMBOLS = (
    '\\','.',
    ':',
    '+', '-',
    '(', ')', '[', ']', ',', '=',
    '==', '<', '>', '<=', '>=', '!=',
)

KEYWORDS = (
    'while',
    'if', 'else',
    'and', 'or',
)


NATIVE_PRELUDE = r"""

function Run(state) {
  state.pause = false
  while (!state.pause && state.programCounter < state.bytecodes.length)
    Step(state)
  console.log(state.pause, state.programCounter, state.bytecodes.length)
}

function Step(state) {
  var bytecode = Fetch(state)
  console.log(bytecode)

  switch(bytecode.type) {
  case 'Label': break
  case 'LookupVariable': state.stack.push(state.scope[bytecode.name]); break
  case 'Number': state.stack.push({type: 'Number', value: bytecode.value}); break
  case 'String': state.stack.push({type: 'String', value: bytecode.value}); break
  case 'PushStack': break
  case 'PopStack': break
  case 'StartList': break
  case 'EndList': break
  case 'StartFunction': break
  case 'Return': break
  case 'DeclareVariable': break
  case 'JumpIf': break
  case 'Function': break
  case 'Apply': break
  case 'Assign': break
  default: throw 'Unrecognized bytecode type ' + bytecode.type
  }
}

function Fetch(state) {
  return state.bytecodes[state.programCounter++]
}

function NewState(bytecodes) {

  var labeltable = {}

  for (var i = 0; i < bytecodes.length; i++)
    if (bytecodes[i].type === 'Label')
      labeltable[bytecodes[i].id] = i

  return {

    pause: false,

    stack: [],
    scope: {},
    stackstack: [],
    scopestack: [],

    labeltable: labeltable,
    programCounter: 0,
    bytecodes: bytecodes
  }
}

;"""


NATIVE_EPILOGUE = ";Run(NewState(bytecodes))"


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
  Fold(f, args[0], Slice(args, 1, None))

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
        index = {'type': 'LookupVariable', 'name': 'None'}
        if not At(':'):
          index = Expression()

        if Consume(']'):
          expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GetItem'}, 'arguments': [expr, index]}
        else:
          Expect(':')

          upper = {'type': 'LookupVariable', 'name': 'None'}
          if not At(':') and not At(']'):
            upper = Expression()

          step = {'type': 'LookupVariable', 'name': 'None'}
          if Consume(':'):
            if not At(']'):
              step = Expression()

          Expect(']')
          expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'Slice'}, 'arguments': [expr, index, upper, step]}
      elif Consume('.'):
        attr = Expect('id').value
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'GetAttribute'}, 'arguments': [expr, {'type': 'String', 'value': attr}]}
      else:
        break
    return expr

  def PrefixExpression():
    if Consume('-'):
      return {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'Negate'}, 'arguments': [PrefixExpression()]}
    return PostfixExpression()

  def AdditiveExpression():
    expr = PrefixExpression()
    while True:
      if Consume('+'):
        rhs = PrefixExpression()
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

  def Suspend(expr):
    return {'type': 'Function', 'arguments': [], 'body': expr}

  def LogicalAndExpression():
    expr = CompareExpression()
    while True:
      if Consume('and'):
        rhs = CompareExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'And'}, 'arguments': [expr, Suspend(rhs)]}
      else:
        break
    return expr

  def LogicalOrExpression():
    expr = LogicalAndExpression()
    while True:
      if Consume('or'):
        rhs = LogicalAndExpression()
        expr = {'type': 'Call', 'function': {'type': 'LookupVariable', 'name': 'Or'}, 'arguments': [expr, Suspend(rhs)]}
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


def ModuleToBytecodes(module):

  def MakeNewlabel():
    MakeNewlabel.counter += 1
    return {'type': 'Label', 'id': MakeNewlabel.counter}
  MakeNewlabel.counter = 0

  def NodeToBytecodes(node):
    if node['type'] == 'Module':
      bytecodes = [{'type': 'DeclareVariable', 'name': name} for name in node['variables']]
      for expr in node['expressions']:
        bytecodes.append({'type': 'PushStack'})
        bytecodes.extend(NodeToBytecodes(expr))
        bytecodes.append({'type': 'PopStack'})
      return bytecodes

    elif node['type'] == 'Block':
      bytecodes = []
      if node['expressions']:
        for expr in node['expressions'][:-1]:
          bytecodes.append({'type': 'PushStack'})
          bytecodes.extend(NodeToBytecodes(expr))
          bytecodes.append({'type': 'PopStack'})
        bytecodes.extend(NodeToBytecodes(node['expressions'][-1]))
      return bytecodes

    elif node['type'] == 'If':
      before_body = MakeNewlabel()
      before_else = MakeNewlabel()
      after_else = MakeNewlabel()
      bytecodes = NodeToBytecodes(node['test'])
      bytecodes.append({'type': 'JumpIf', 'id': before_body['id']})
      bytecodes.append({'type': 'LookupVariable', 'name': 'True'})
      bytecodes.append({'type': 'JumpIf', 'id': before_else['id']})
      bytecodes.append(before_body)
      bytecodes.extend(NodeToBytecodes(node['body']))
      bytecodes.append({'type': 'LookupVariable', 'name': 'True'})
      bytecodes.append({'type': 'JumpIf', 'id': after_else['id']})
      bytecodes.append(before_else)
      bytecodes.extend(NodeToBytecodes(node['else']))
      bytecodes.append(after_else)
      return bytecodes

    elif node['type'] == 'While':
      before_test = MakeNewlabel()
      before_body = MakeNewlabel()
      after_body = MakeNewlabel()
      bytecodes = [before_test]
      bytecodes.extend(NodeToBytecodes(node['test']))
      bytecodes.append({'type': 'JumpIf', 'id': before_body['id']})
      bytecodes.append({'type': 'LookupVariable', 'name': 'True'})
      bytecodes.append({'type': 'JumpIf', 'id': after_body['id']})
      bytecodes.append(before_body)
      bytecodes.extend(NodeToBytecodes(node['body']))
      bytecodes.append(after_body)
      return bytecodes

    elif node['type'] in ('LookupVariable', 'Number', 'String',):
      return [node]

    elif node['type'] == 'List':
      bytecodes = [{'type': 'StartList'}]
      for expr in node['value']:
        bytecodes.extend(bytecodes)
      bytecodes.append({'type': 'EndList'})
      return bytecodes

    elif node['type'] == 'Function':
      before_body = MakeNewlabel()
      after_body = MakeNewlabel()
      bytecodes = []
      bytecodes.append({'type': 'LookupVariable', 'name': 'True'})
      bytecodes.append({'type': 'JumpIf', 'id': after_body['id']})
      bytecodes.append(before_body)
      bytecodes.append({'type': 'StartFunction', 'arguments': node['arguments']})
      bytecodes.extend({'type': 'DeclareVariable', 'name': name} for name in node['variables'])
      bytecodes.append({'type': 'LookupVariable', 'name': 'None'})
      bytecodes.extend(NodeToBytecodes(node['body']))
      bytecodes.append({'type': 'Return'})
      bytecodes.append(after_body)
      bytecodes.append({'type': 'Function', 'id': before_body['id']})
      return bytecodes

    elif node['type'] == 'Call':
      bytecodes = NodeToBytecodes(node['function'])
      bytecodes = [{'type': 'StartList'}]
      for expr in node['arguments']:
        bytecodes.extend(bytecodes)
      bytecodes.append({'type': 'EndList'})
      bytecodes.append({'type': 'Apply'})
      return bytecodes

    elif node['type'] == 'Assign':
      bytecodes = NodeToBytecodes(node['value'])
      bytecodes.append({'type': 'Assign', 'target': node['target']})
      return bytecodes

    raise SyntaxError('Unrecognized type ' + node['type'])

  return NodeToBytecodes(module)


def SanitizeStringForJavascript(s):
  return '+'.join('String.fromCharCode(%d)' % ord(c) for c in s)


def BytecodesToJavascript(bytecodes):
  s = NATIVE_PRELUDE + ';var bytecodes = ['
  for i, bytecode in enumerate(bytecodes):
    if i > 0:
      s += ','
    s += '{'
    type_ = bytecode['type']
    for j, (key, value) in enumerate(bytecode.items()):
      if j > 0:
        s += ','
      s += repr(key) + ':'
      if type_ == 'String' and key == 'value':
        s += SanitizeStringForJavascript(value)
      else:
        s += repr(value)
    s += '}'
  s += ']' + NATIVE_EPILOGUE + '\n'
  return s


def Translate(source):
  return BytecodesToJavascript(ModuleToBytecodes(Parse(source)))


if __name__ == '__main__':
  sys.stdout.write(Translate(PRELUDE + sys.stdin.read()))
