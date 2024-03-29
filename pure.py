"""pure.py"""


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

  def __init__(self, type, value, origin):
    self.type = type
    self.value = value
    self.origin = origin

  def __eq__(self, other):
    return self.type == other.type and self.value == other.value

  def __repr__(self):
    return 'Token(%r,%r)' % (self.type, self.value)


class LexError(Exception):

  def __init__(self, message, origin):
    super(LexError, self).__init__(message + '\n' + origin.LocationMessage())


def Lex(string ,filename):
  tokens = []
  s = string
  i = 0

  def MakeOrigin():
    return Origin(filename, s, j)

  def MakeToken(type_, value):
    return Token(type_, value, MakeOrigin())

  while True:
    while i < len(s) and s[i].isspace():
      i += 1

    j = i

    if i >= len(s):
      break

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
          raise LexError("Where is the matching quotes for " + quote + '?', MakeOrigin())
        i += 2 if not raw and s[i] == '\\' else 1
      i += len(quote)
      tokens.append(MakeToken('String', eval(s[j:i])))

    elif s[i] in ('(', ')'):
      i += 1
      tokens.append(MakeToken(s[j:i], None))

    else:
      while i < len(s) and s[i] not in ('(', ')') and not s[i].isspace():
        i += 1

      tokens.append(MakeToken('Name', s[j:i]))

  return tokens


class Node(object):

  def __init__(self, type, value, origin):
    self.type = type
    self.value = value
    self.origin = origin

  def __eq__(self, other):
    return self.type == other.type and self.value == other.value

  def __repr__(self):
    return 'Node(%r,%r,%r)' % (self.type, self.value, self.origin)


class ParseError(Exception):

  def __init__(self, message, origin):
    super(ParseError, self).__init__(message + '\n' + origin.LocationMessage())


def Parse(string, filename):
  toks = Lex(string, filename)
  stack = [Node('Module', [], Origin(filename, string, 0))]

  for tok in toks:
    if tok.type == '(':
      stack.append(Node('Form', [], tok.origin))
    elif tok.type == ')':
      if len(stack) < 2:
        raise ParseError("Where's the matching parenthesis?", tok.origin)
      call = stack.pop()
      assert call.type == 'Form', call.type
      if not len(call.value):
        raise ParseError("Every form must have at least one element", call.origin)
      fexpr = call.value[0]
      argexprs = call.value[1:]
      call.value = [fexpr, argexprs]
      stack[-1].value.append(call)
    elif tok.type in ('Name', 'Number', 'String'):
      stack[-1].value.append(Node(tok.type, tok.value, tok.origin))
    else:
      raise ValueError('Unexpected token type: ' + tok.type)

  if len(stack) > 1:
    raise ParseError("Where's the matching parenthesis?", stack[-1].origin)

  return stack[0]


class Scope(object):

  def __init__(self, parent=None):
    self.parent = parent
    self.table = dict()
    self.stack = parent.stack if parent else []

  def Declare(self, key, value=None):
    self.table[key] = nil if value is None else value

  def DeclareForm(self, form):
    self.table[form.__name__] = Form(form)
    return form

  def DeclareFunction(self, function):
    self.table[function.__name__] = Function(function)
    return function

  def Get(self, key):
    if key in self.table:
      return self.table[key]
    elif self.parent is not None:
      return self.parent.Get(key)
    else:
      raise KeyError(key)

  def Set(self, key, value):
    if key in self.table:
      self.table[key] = value
    elif self.parent is not None:
      self.parent.Set(key, value)
    else:
      raise KeyError(key)


class Object(object):
  pass


class Nil(Object):

  def __init__(self):
    self.metatable = NIL_METATABLE


class Bool(Object):

  def __init__(self, value):
    self.value = value
    self.metatable = BOOL_METATABLE


class Number(Object):

  def __init__(self, value):
    self.value = value
    self.metatable = NUMBER_METATABLE


class String(Object):

  def __init__(self, value):
    self.value = value
    self.metatable = STRING_METATABLE


class Table(Object):

  def __init__(self):
    self.table = dict()
    self.parent = None
    self.metatable = TABLE_METATABLE

  def DeclareMethod(self, name):
    def wrapper(method):
      assert isinstance(method, Form), type(method)
      self.table[name] = method
    return wrapper

  def Lookup(self, name):
    if name in self.table:
      return self.table[name]
    elif self.parent:
      return self.parent.Lookup(name)
    else:
      raise KeyError(name)


class Form(Object):

  def __init__(self, f):
    self.Apply = f
    self.metatable = FORM_METATABLE


class Function(Form):

  def __init__(self, f):
    self.f = f
    self.metatable = FORM_METATABLE

  def Apply(self, scope, origin, argexprs):
    args = [Eval(scope, argexpr) for argexpr in argexprs]
    scope.stack.append(origin)
    try:
      return self.f(*args)
    finally:
      scope.stack.pop()


def Eval(scope, node):
  if node.type == 'Module':
    last = nil
    for expr in node.value:
      last = Eval(scope, expr)
    return last
  elif node.type == 'Form':
    fexpr, argexprs = node.value
    return Eval(scope, fexpr).Apply(scope, node.origin, argexprs)
  elif node.type == 'Name':
    return scope.Get(node.value)
  elif node.type == 'Number':
    return Number(node.value)
  elif node.type == 'String':
    return String(node.value)
  else:
    raise ValueError('Unexpected node type: ' + node.type)


ROOT_SCOPE = Scope()

TABLE_METATABLE = None
TABLE_METATABLE = Table()
TABLE_METATABLE.metatable = TABLE_METATABLE

NIL_METATABLE = Table()
BOOL_METATABLE = Table()
NUMBER_METATABLE = Table()
STRING_METATABLE = Table()
FORM_METATABLE = Table()

nil = Nil()

@STRING_METATABLE.DeclareMethod('Print')
@Function
def _(owner):
  result = GetMetatable(owner)['String'](owner)
  assert type(result) == String
  print(result.value)
  return result


@STRING_METATABLE.DeclareMethod('String')
@Function
def _(owner):
  return Function(lambda: owner)


@ROOT_SCOPE.DeclareForm
def While(scope, origin, argexprs):
  test, body = argexprs
  last = None
  while Eval(scope, test):
    last = Eval(scope, body)
  return last


@ROOT_SCOPE.DeclareFunction
def GetMetatable(owner):
  return owner.metatable


@ROOT_SCOPE.DeclareFunction
def Get(owner, attribute):
  assert type(attribute) == String, type(attribute)
  method = GetMetatable(owner).Lookup(attribute.value)


def Run(string, filename):
  return Eval(ROOT_SCOPE, Parse(string, filename))

Run(r"""

((Get 'hi' 'Print'))

""", '<test>')

