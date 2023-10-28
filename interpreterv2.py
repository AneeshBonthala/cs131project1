from brewparse import parse_program
from intbase import InterpreterBase, ErrorType
from element import Element
from copy import deepcopy

class Interpreter(InterpreterBase):

    def error_not_found(self, name, type = 'variable'):
        super().error(ErrorType.NAME_ERROR, f"{type.title()} '{name}' has not been defined.")

    def error_args(self, name, type = 'number'):
        super().error(ErrorType.NAME_ERROR, f"Invalid {type.lower()} of argument(s) provided for function '{name}'.")

    def error_types(self, type1, type2):
        super().error(ErrorType.TYPE_ERROR, f"Incompatible types for operation: '{type1}' and '{type2}'.")

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.variables = {}


    def eval_expr(self, expr):
        elem_type = expr.elem_type

        if elem_type == 'int' or elem_type == 'string' or elem_type == 'bool' or elem_type == 'nil':
            return expr

        if elem_type == 'var':
            var = expr.get('name')
            if var not in self.variables.keys(): self.error_not_found(var)
            return self.variables[var]
        
        if elem_type == 'fcall':
            return self.run_function(expr)
        
        if elem_type == 'neg':
            try:
                op1 = self.eval_expr(expr.get('op1'))
                result = Element('int', val = -op1.get('val'))
            except TypeError: self.error_types('-', op1.elem_type)
            else: return result

        if elem_type == '!':
            op1 = self.eval_expr(expr.get('op1'))
            # It is illegal to use the logical not operation on non-boolean types. Doing so must result in an error of ErrorType.TYPE_ERROR
            if op1.elem_type != 'bool': self.error_types('!', op1.elem_type)
            return Element('bool', val = not op1.get('val'))
        
        else:
            op1 = self.eval_expr(expr.get('op1'))
            op2 = self.eval_expr(expr.get('op2'))
            op1val = op1.get('val')
            op1type = op1.elem_type
            op2val = op2.get('val')
            op2type = op2.elem_type

            if elem_type == '+':
                # It is illegal to use arithmetic operations on non-integer types, with the exception of using + to concatenate strings. Doing so must result in an error of ErrorType.TYPE_ERROR.
                if op1type != 'int' and op1type != 'string':
                    self.error_types(op1type, op2type)
                if op2type != 'int' and op2type != 'string':
                    self.error_types(op1type, op2type)
                if op1type != op2type:
                    self.error_types(op1type, op2type)
                return Element(op1type, val = op1val + op2val)
            elif elem_type == '-' or elem_type == '*' or elem_type == '/':
                if op1type != 'int' or op2type != 'int':
                    self.error_types(op1type, op2type)
                dict = {
                    '-': lambda x, y: x - y,
                    '*': lambda x, y: x * y,
                    # Division of integers must result in a truncated integer result, like using a // b with Python
                    # You need not handle division by zero errors. Should such a division occur your interpreter can have undefined behavior, including behaviors that are different from our solution
                    '/': lambda x, y: x // y
                }
                return Element('int', val = dict[elem_type](op1val, op2val))
            else:
                def true(): return deepcopy(Element('bool', val = True))
                def false(): return deepcopy(Element('bool', val = False))
                if elem_type == '==':
                # It is legal to compare values of different types to each other with == and !=. If two values are of different types, then must treat them as not equal. This includes comparing any value to nil.
                    if op1type != op2type: return false()
                    return true() if op1val == op2val else false()
                elif elem_type == '!=':
                    if op1type != op2type: return true()
                    return true() if op1val != op2val else false()
                else:
                    # It is illegal to compare values of different types with any other comparison operator (e.g., >, <=, etc.). Doing so must result in an error of ErrorType.TYPE_ERROR.
                    if op1type != op2type: self.error_types(op1type, op2type)
                    dict = {
                        '<': lambda x, y: true() if x < y else false(),
                        '<=': lambda x, y: true() if x <= y else false(),
                        '>': lambda x, y: true() if x > y else false(),
                        '>=': lambda x, y: true() if x >= y else false(),
                        '||': lambda x, y: true() if x or y else false(),
                        '&&': lambda x, y: true() if x and y else false()
                    }
                    return dict[elem_type](op1val, op2val)
        
        

    def run_assignment(self, statement):
        self.variables[statement.get('name')] = self.eval_expr(statement.get('expression'))


    def run_function(self, statement):
        name = statement.get('name')
        args = statement.get('args')
        statements = statement.get('statements')
        

        if name == 'inputi':
            if len(args) > 1: self.error_args('inputi')
            if len(args) == 1:
                prompt = self.eval_expr(args[0])
                if prompt.elem_type != 'string': self.error_args('inputi', 'type')
                super().output(prompt.get('val'))
            #You may assume that only valid integers will be entered in response to an inputi() prompt and do NOT need to test for non-integer values being entered
            return Element('int', val = int(super().get_input()))
        
        # You must implement the inputs() function which inputs and returns a string as its return value. It must use our InterpreterBase.get_input() method to get input. It may take either one or no parameters
        if name == 'inputs':
            if len(args) > 1: self.error_args('inputs')
            if len(args) == 1:
                prompt = self.eval_expr(args[0])
                if prompt.elem_type != 'string': self.error_args('inputs', 'type')
                super().output(prompt.get('val'))
            return Element('string', val = super().get_input())
        
        if name == 'print':
            result = ''
            for arg in args:
                eval_arg = self.eval_expr(arg).get('val')
                # When you print booleans, the output must be either "true" or "false" (all lower case, quotes should not be included)
                if eval_arg == True or eval_arg == False:
                    eval_arg = str(eval_arg).lower()
                result += str(eval_arg)
                # You will not be tested on printing nil values. In such scenarios, your interpreter may behave in any way you like, and may act in a different way than our solution.
            super().output(result)
            # print() function can be called within expressions. The return value of print() should always be nil.
            return Element('nil')
        
        else:
            if (name, len(args)) not in self.variables:
                self.error_not_found(name, 'function')
            self.define_function(self.variables[(name, len(args))], args)


    # def define_function(self, func, args):
    #     for statement in func.get('statements'):
    #         self.run_statement(statement)
        

    def run_if(self, statement):
        condition_true = self.eval_expr(statement.get('condition')).get('val')
        else_statements = statement.get('else_statements')
        before_len = len(self.variables.keys())
        start_of_scope = None

        if condition_true:
            for s in statement.get('statements'):
                self.run_statement(s)
                if start_of_scope is None and before_len != len(self.variables.keys()):
                    start_of_scope = len(self.variables.keys()) - 1
        elif else_statements:
            for s in else_statements:
                self.run_statement(s)
                if start_of_scope is None and before_len != len(self.variables.keys()):
                    start_of_scope = len(self.variables.keys()) - 1
        
        self.garbage_collection(start_of_scope)

        
    def run_while(self, statement):
        pass






    def run_statement(self, statement):
        elem_type = statement.elem_type

        if elem_type == '=': self.run_assignment(statement)

        elif elem_type == 'fcall': self.run_function(statement)

        elif elem_type == 'if': self.run_if(statement)

        elif elem_type == 'while': self.run_while(statement)


    def run(self, program):
        ast = parse_program(program)

        main_node = None
        for func in ast.get('functions'):
            if func.get('name') == 'main': main_node = func
            # You may overload a function, defining multiple versions of it that take different numbers of parameters
            else: self.variables[(func.get('name'), len(func.get('args')))] = func
        if not main_node: self.error_not_found('main', 'function')

        for statement in main_node.get('statements'):
            self.run_statement(statement)


    def garbage_collection(self, start_of_scope):
        if start_of_scope is None: return
        for i in range(len(self.variables.keys())):
            if i >= start_of_scope:
                key = list(self.variables.keys())[i]
                del self.variables[key]


def test():
    inter = Interpreter()
    with open('test.txt') as file:
        prog = file.read()
    inter.run(prog)

test()