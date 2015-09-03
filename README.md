
## Grammar

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

## Bytecodes

Label
  id: int
LookupVariable: pushes 1 value
  name: str
Number: pushes 1 value
  value: int|float
String: pushes 1 value
  value: str
PushStack
PopStack (Must be matched with a PushStack)
StartList
EndList (Must be matched with a StartList): pushes 1 value
StartFunction
  arguments: [str]
Return (Must be matched with a StartFunction): expects 1 value
DeclareVariable
  name: str
JumpIf: expects 1 value
Function: pushes 1 value
  id: str
Apply: expects 2 values and pushes 1 value
Assign: expects 1 value and pushes 1 value

## CCL types

Number
  value: number

String
  value: string

List
  value: [Value]

Function
  id: index
  

## Builtins

At the moment, I don't have multimethods implemented, so it would be quite a hassle to implement all of these methods.

As such, most of this list is a wishlist at the moment.

### Named constants
None
True
False

### Attributes
GetAttribute(Object, String)
SetAttribute(Object, String, Object)

### Type conversions
Type(Object)
Bool(Object)
Int(Bool|Int|Float|String)
Float(Bool|Int|Float|String)
String(Object)
List(Iterable)
Set(Iterable)
Dict(Iterable)
Iterator(Iterable)

### Functional utils
Reduce(Function, Iterable)
Fold(Function, Object, Iterable)
FoldLeft(Function, Object, Iterable)
FoldRight(Function, Object, Iterable)
Map(Function, Iterable)
Filter(Function, Iterable)

### Arithmetic functions
Negate(Number)
Add(Number, Number)
Add(String, String)
Add(List, List)
Subtract(Number, Number)
Multiply(Number, Number)
Multiply(List, Int)
Divide(Number, Number)
Mod(Number, Number)
Mod(String, List)

### Container utils
GetItem(List, Int)
SetItem(List, Int, Object)
Slice(List|String, Int|None, Int|None, Int|None)
Push(List, Object)
Push(String, String)
Pop(List)
Pop(String)

### Logical operations
Not(Object)
Equal(Object, Object)
LessThan(Object, Object)

### String utils
Split(String)
SplitLines(String)

### Iterable utils
Done(Iterator)
Next(Iterator)

### IO
Stdin : File
Stdout : File
Read(File) : String
Read(String) : String
Read() : String
Prints(List) : List
Prints(File, List): List
Print(Object) : Object
Print(File, Object): Object

## Recursion depth.

Kyumins-iMac:ccl math4tots$ printf "1001 %.0s" {1..1001} | node x.js 
/Users/math4tots/src/ccl/x.js:0
(function (exports, require, module, __filename, __dirname) { // This is an au

RangeError: Maximum call stack size exceeded
    at TypeOf (/Users/math4tots/src/ccl/x.js)
    at XXAdd (/Users/math4tots/src/ccl/x.js:169:10)
    at /Users/math4tots/src/ccl/x.js:274:3055
    at /Users/math4tots/src/ccl/x.js:274:3032
    at /Users/math4tots/src/ccl/x.js:274:3039
    at /Users/math4tots/src/ccl/x.js:274:2992
    at /Users/math4tots/src/ccl/x.js:274:3001
    at /Users/math4tots/src/ccl/x.js:274:2952
    at XXi (/Users/math4tots/src/ccl/x.js:274:2963)
    at /Users/math4tots/src/ccl/x.js:274:3080

