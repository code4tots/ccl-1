"use strict";

var OP_NAME           =  0 // (str)
var OP_NUM            =  1 // (num)
var OP_STR            =  2 // (str)
var OP_MAKE_LIST      =  3
var OP_PUSH_STACK     =  4
var OP_POP_STACK      =  5
var OP_PUSH_SCOPE     =  6
var OP_POP_SCOPE      =  7
var OP_JUMP_IF        =  9 // (int)
var OP_JUMP           = 10 // (int)
var OP_CALL           = 11 // (int)

var SCOPE_WITH_BUILTINS = {}

function Machine(bytecodes) {

  var i = 0, code
  while (i < bytecodes.length) {
    code = bytecodes[i]

    if (code === OP_LABEL) {
      this.label_table[bytecodes[i+1]] = i+2
    }

    switch (code) {
    case OP_NUM:
    case OP_STR:
    case OP_LABEL:
    case OP_JUMP_IF:
    case OP_JUMP:
    case OP_CALL: i += 2; break
    default: i++; break
    }
  }

  this.bytecodes = bytecodes
  this.stack = []
  this.scope = Object.create(SCOPE_WITH_BUILTINS)
  this.stack_stack = []
  this.scope_stack = []
  this.program_counter = 0
}

Machine.prototype.fetch = function() {
  return this.bytecodes[this.program_counter++]
}

var machine = new Machine([])
