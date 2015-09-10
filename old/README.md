## Goals

Goal of this project is to implement something basic I can port to multiple platforms.

That is, a language whose AST is simple enough that I can write a good chunk of code in this one language, and expect to use it for a variety of projects (e.g. Android, iOS, Web, desktop).

Right now there is only a nodejs backend.

Once the language is mature enough, I might consider porting to other languages.

## On the fence

About implementing destructuring assignment.

The translator currently translates to javascript in a way such that destructuring assignment is supported iff it is supported in the underlying javascript implementation (it's part of ES6 standard, but node doesn't seem to support it yet).

A portable implementation would add a certain level of complexity...

Also, I don't want syntactic translations to create functions where user hasn't created any, due to the way variable declarations are deduced. Making things work nicely will be a lot more work and add a good deal of complexity to the code.

## Grammar

    Module

    Name
    Number
    String
    List
    Function
    Block
    Attribute
    Call
    Subscript

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
Or(Object, Function)
And(Object, Function)
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
