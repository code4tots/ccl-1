
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

  def Apply(self, scope, node):
    return self.f(scope, node)


class Function(Form):

  def __init__(self, f):
    self.f = f
    self.metatable = FORM_METATABLE

  def Apply(self, scope, node):
    _, argexprs = node.value
    args = [Eval(scope, argexpr) for argexpr in argexprs]
    scope.stack.append(node.origin)
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
    return Eval(scope, fexpr).Apply(scope, node)
  elif node.type == 'Name':
    return scope.Get(node.value)
  elif node.type == 'Number':
    return Number(node.value)
  elif node.type == 'String':
    return String(node.value)
  else:
    raise ValueError('Unexpected node type: ' + node.type)
