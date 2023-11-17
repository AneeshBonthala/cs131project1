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
        self.linked_refs = {}


    def eval_expr(self, expr):
        elem_type = expr.elem_type

        if elem_type == 'int' or elem_type == 'string' or elem_type == 'bool' or elem_type == 'nil':
            return expr

        if elem_type == 'var':
            var = expr.get('name')

            # reference assignment
            if var in self.linked_refs:
                return self.variables[self.linked_refs[var]]
            
            # function assignment
            func_name = None
            for key in self.variables.keys():
                if isinstance(key, tuple) and key[0] == var:
                    if func_name:
                        self.error_not_found(var)
                    func_name = key
            if func_name:
                return self.variables[func_name]

            # variable does not exist
            if var not in self.variables:
                self.error_not_found(var)

            # regular assignment
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
            if op1.elem_type == 'int':
                condition_true = self.int_to_bool(op1.get('val'))
            else:
                condition_true = op1.get('val')
            if condition_true != True and condition_true != False:
                self.error_types('!', op1.elem_type)
            return Element('bool', val = not condition_true)
        
        else:
            op1 = self.eval_expr(expr.get('op1'))
            op2 = self.eval_expr(expr.get('op2'))
            op1val = op1.get('val')
            op1type = op1.elem_type
            op2val = op2.get('val')
            op2type = op2.elem_type

            if elem_type == '+':
                def add(x, y):
                    return deepcopy(Element('int', val = x + y))
                
                # only valid types are int, str, bool
                if op1type != 'int' and op1type != 'string' and op1type != 'bool':
                    self.error_types(op1type, op2type)
                if op2type != 'int' and op2type != 'string' and op2type !='bool':
                    self.error_types(op1type, op2type)
                
                # only valid add of two non-identical types is int + bool
                if op1type == 'bool' and op2type == 'int':
                    return add(self.bool_to_int(op1val) + op2val)
                if op1type == 'int' and op2type == 'bool':
                    return add(op1val + self.bool_to_int(op2val))
                if op1type != op2type:
                    self.error_types(op1type, op2type)
                
                # not using add func in case of str + str
                return deepcopy(Element(op1type, val = op1val + op2val))
            
            elif elem_type == '-' or elem_type == '*' or elem_type == '/':
                dict = {
                    '-': lambda x, y: x - y,
                    '*': lambda x, y: x * y,
                    '/': lambda x, y: x // y
                }
                
                # only valid -*/ of two non-identical types is int:bool
                if op1type == 'bool' and op2type == 'int':
                    return deepcopy(Element('int', val = dict[elem_type](self.bool_to_int(op1val), op2val)))
                if op1type == 'int' and op2type == 'bool':
                    return deepcopy(Element('int', val = dict[elem_type](op1val, self.bool_to_int(op2val))))

                # otherwise, must be only ints
                if op1type != 'int' or op2type != 'int':
                    self.error_types(op1type, op2type)
                
                return deepcopy(Element('int', val = dict[elem_type](op1val, op2val)))
            
            else:
                def true():
                    return deepcopy(Element('bool', val = True))
                def false():
                    return deepcopy(Element('bool', val = False))
                if elem_type == '==':
                    # Integers with a value of zero are always converted to false | All non-zero values are converted to true
                    if op1type == 'bool' and op2type == 'int':
                        return true() if self.int_to_bool(op2val) and op1val else false()
                    if op1type == 'int' and op2type == 'bool':
                        return true() if self.int_to_bool(op1val) and op2val else false()
                    # It is legal to compare values of different types to each other with == and !=. At this point, if two values are of different types, then must treat them as not equal. This includes comparing any value to nil.
                    if op1type != op2type:
                        return false()
                    return true() if op1val == op2val else false()
                elif elem_type == '!=':
                    if op1type == 'bool' and op2type == 'int':
                        return true() if self.int_to_bool(op2val) and op1val else false()
                    if op1type == 'int' and op2type == 'bool':
                        return true() if self.int_to_bool(op1val) and op2val else false()
                    if op1type != op2type:
                        return true()
                    return true() if op1val != op2val else false()
                elif elem_type == '||' or elem_type == '&&':
                    dict = {
                        '||': lambda x, y: true() if x or y else false(),
                        '&&': lambda x, y: true() if x and y else false()
                    }
                    if op1type == 'bool' and op2type == 'int':
                        return dict[elem_type](op1val, self.int_to_bool(op2val))
                    if op1type == 'int' and op2type == 'bool':
                        return dict[elem_type](self.int_to_bool(op1val), op2val)
                    if op1type != 'bool' or op2type != 'bool':
                        self.error_types(op1type, op2type)
                    return dict[elem_type](op1val, op2val)
                else:
                    # It is illegal to compare values of different types with any other comparison operator (e.g., >, <=, etc.). Doing so must result in an error of ErrorType.TYPE_ERROR.
                    if op1type != 'int' or op2type != 'int':
                        self.error_types(op1type, op2type)
                    dict = {
                        '<': lambda x, y: true() if x < y else false(),
                        '<=': lambda x, y: true() if x <= y else false(),
                        '>': lambda x, y: true() if x > y else false(),
                        '>=': lambda x, y: true() if x >= y else false(),
                    }
                    return dict[elem_type](op1val, op2val)

    def int_to_bool(val):
        return False if val == 0 else True

    def bool_to_int(val):
        return 1 if val else 0

    def run_assignment(self, statement):
        name = statement.get('name')
        expr = statement.get('expression')
        val = self.eval_expr(expr)

        # storing a function in a variable
        if val.elem_type == 'func':
            self.linked_refs[name] = (val.get('name'), len(val.get('args')))

        if name in self.linked_refs:
            name = self.linked_refs[name]

        self.variables[name] = val


    def run_function(self, statement):
        name = statement.get('name')
        args = statement.get('args')
        
        if name == 'inputi':
            if len(args) > 1: self.error_args('inputi')
            if len(args) == 1:
                prompt = self.eval_expr(args[0])
                if prompt.elem_type != 'string': self.error_args('inputi', 'type')
                super().output(prompt.get('val'))
            #You may assume that only valid integers will be entered in response to an inputi() prompt and do NOT need to test for non-integer values being entered
            return deepcopy(Element('int', val = int(super().get_input())))
        
        # You must implement the inputs() function which inputs and returns a string as its return value. It must use our InterpreterBase.get_input() method to get input. It may take either one or no parameters
        if name == 'inputs':
            if len(args) > 1: self.error_args('inputs')
            if len(args) == 1:
                prompt = self.eval_expr(args[0])
                if prompt.elem_type != 'string': self.error_args('inputs', 'type')
                super().output(prompt.get('val'))
            return deepcopy(Element('string', val = super().get_input()))
        
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
            return deepcopy(Element('nil'))
        
        else:
            if name in self.linked_refs:
                return self.define_function(self.variables[self.linked_refs[name]], args)
            if (name, len(args)) not in self.variables:
                self.error_not_found(name, 'function')
            return self.define_function(self.variables[(name, len(args))], args)


    def define_function(self, func, args):
        params = func.get('args')
        save_vals = {}
        start_of_scope = len(self.variables.keys())
        start_of_scope_2 = len(self.linked_refs.keys())

        for i in range(len(args)):
            param_name = params[i].get('name')

            # value arguments
            if params[i].elem_type == 'arg':
                if param_name in self.variables:
                    save_vals[param_name] = self.variables[param_name]
                self.variables[param_name] = self.eval_expr(args[i])

            # reference arguments
            if params[i].elem_type == 'refarg':
                # if the arg is not a variable, treat it as a normal arg
                if args[i].elem_type != 'var':
                    self.variables[param_name] = self.eval_expr(args[i])
                else:
                    self.linked_refs[param_name] = args[i].get('name')
                


        for statement in func.get('statements'):
            ret = self.run_statement(statement)
            if ret is not None:
                break

        for key, val in save_vals.items():
            self.variables[key] = val

        self.refs_garbage_collection(start_of_scope_2)
        self.garbage_collection(start_of_scope)
        return deepcopy(Element('nil')) if ret is None else ret



    def run_if(self, statement):
        condition = self.eval_expr(statement.get('condition'))
        # If the expression/variable/value that is the condition of the if statement does not evaluate to a boolean, you must generate an error of type ErrorType.TYPE_ERROR by calling InterpreterBase.error().
        if condition.elem_type == 'int':
            condition_true = self.int_to_bool(condition.get('val'))
        else:
            condition_true = condition.get('val')
        if condition_true != True and condition_true != False:
            self.error_types('if', condition.elem_type)
        else_statements = statement.get('else_statements')
        start_of_scope = len(self.variables.keys())
        ret = None

        if condition_true:
            for s in statement.get('statements'):
                ret = self.run_statement(s)
                if ret is not None:
                    break
        elif else_statements:
            for s in else_statements:
                ret = self.run_statement(s)
                if ret is not None:
                    break
        
        self.garbage_collection(start_of_scope)

        return ret

        
    def run_while(self, statement):
        condition = self.eval_expr(statement.get('condition'))
        if condition.elem_type == 'int':
            condition_true = self.int_to_bool(condition.get('val'))
        else:
            condition_true = condition.get('val')
        # If the expression/variable/value that is the condition of the while statement does not evaluate to a boolean, you must generate an error of type ErrorType.TYPE_ERROR by calling InterpreterBase.error().
        if condition_true != True and condition_true != False:
            self.error_types('while', condition.elem_type)
        start_of_scope = len(self.variables.keys())
        ret = None

        if condition_true:
            for s in statement.get('statements'):
                ret = self.run_statement(s)
                if ret is not None:
                    self.garbage_collection(start_of_scope)
                    return ret
            self.garbage_collection(start_of_scope)
            return self.run_while(statement)
        
        return ret

    
    def run_return(self, statement):
        ret = statement.get('expression')
        if ret is None:
            return deepcopy(Element('nil'))
        result = self.eval_expr(ret)
        return deepcopy(result)

    def run_statement(self, statement):
        elem_type = statement.elem_type
        if elem_type == '=':
            self.run_assignment(statement)
        elif elem_type == 'fcall':
            self.run_function(statement)
        elif elem_type == 'if':
            return self.run_if(statement)
        elif elem_type == 'while':
            return self.run_while(statement)
        elif elem_type == 'return':
            return self.run_return(statement)


    def run(self, program):
        ast = parse_program(program)

        main_node = None
        for func in ast.get('functions'):
            if func.get('name') == 'main':
                main_node = func
            # You may overload a function, defining multiple versions of it that take different numbers of parameters
            else:
                self.variables[(func.get('name'), len(func.get('args')))] = func
        if not main_node:
            self.error_not_found('main', 'function')

        for statement in main_node.get('statements'):
            ret = self.run_statement(statement)
            if ret is not None:
                break


    def garbage_collection(self, start_of_scope):
        keys_to_del = []
        for i in range(len(self.variables.keys())):
            if i >= start_of_scope:
                key = list(self.variables.keys())[i]
                keys_to_del.append(key)
        for key in keys_to_del:
            del self.variables[key]

    def refs_garbage_collection(self, start_of_scope):
        keys_to_del = []
        for i in range(len(self.linked_refs.keys())):
            if i >= start_of_scope:
                key = list(self.linked_refs.keys())[i]
                keys_to_del.append(key)
        for key in keys_to_del:
            del self.linked_refs[key]


def test():
    inter = Interpreter()
    with open('test.txt') as file:
        prog = file.read()
    inter.run(prog)

test()