from brewparse import parse_program
from intbase import InterpreterBase, ErrorType
from element import Element
from copy import deepcopy

class Environment:

    def __init__(self):
        self.variables = [{}]
        self.aliases = [{}]
        self.functions = {}

    def __find_alias(self, name):
        if name in self.aliases[-1]:
            name = self.aliases[-1][name]
        return name
    
    def get_value(self, name):
        # assigning a function to a variable
        if name in self.functions:
            if len(self.functions[name].values()) > 1:
                return None
            return list(self.functions[name].values())[0]
        name = self.__find_alias(name)
        return self.variables[-1].get(name)
    
    def set_value(self, name, val):
        name = self.__find_alias(name)
        for scope in self.variables:
            if name in scope:
                scope[name] = val
        self.variables[-1][name] = val

    def add_func(self, func):
        name = func.get('name')
        num_args = len(func.get('args'))
        if name not in self.functions:
            self.functions[name] = {num_args:func}
        elif num_args in self.functions[name]:
            return False
        else:
            self.functions[name][num_args] = func
        return True
    
    def get_func(self, name, num_args):
        # make sure num_args matches
        if name in self.variables[-1]:
            return_val = self.variables[-1][name]
            if len(return_val.get('args')) != num_args:
                return None
            return return_val
        try:
            return_val = self.functions.get(name).get(num_args)
        except:
            return None
        else:
            return return_val
    
    def add_scope(self, scope):
        self.variables.append(scope[0])
        self.aliases.append(scope[1])
    
    def del_scope(self):
        self.variables.pop()
        self.aliases.pop()
    
    def get_scope_copy(self):
        return (deepcopy(self.variables[-1]), deepcopy(self.aliases[-1]))


    

class Interpreter(InterpreterBase):

    def error_not_found(self, name, type = 'variable'):
        super().error(ErrorType.NAME_ERROR, f"{type.title()} '{name}' has not been defined.")

    def error_args(self, name, type = 'number'):
        super().error(ErrorType.NAME_ERROR, f"Invalid {type.lower()} of argument(s) provided for function '{name}'.")

    def error_types(self, type1, type2):
        super().error(ErrorType.TYPE_ERROR, f"Incompatible types for operation: '{type1}' and '{type2}'.")

    def error_dup_funcs(self, func):
        super().error(ErrorType.NAME_ERROR, f"More than one functions with name '{func}' were defined.")

    def int_to_bool(val):
        return False if val == 0 else True

    def bool_to_int(val):
        return 1 if val else 0

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.env = Environment()
        self.functions = {}


    def __eval_expr(self, expr):
        elem_type = expr.elem_type

        if elem_type == 'int' or elem_type == 'string' or elem_type == 'bool' or elem_type == 'func' or elem_type == 'nil':
            return expr

        if elem_type == 'var':
            name = expr.get('name')
            val = self.env.get_value(name)
            if val:
                return val
            else:
                self.error_not_found(name)

        if elem_type == 'fcall':
            return self.__run_function(expr)
        
        if elem_type == 'lambda':
            return self.__create_lambda(expr)
        
        if elem_type == 'neg':
            try:
                op1 = self.__eval_expr(expr.get('op1'))
                result = Element('int', val = -op1.get('val'))
            except TypeError:
                self.error_types('-', op1.elem_type)
            else: return result

        if elem_type == '!':
            op1 = self.__eval_expr(expr.get('op1'))
            if op1.elem_type == 'int':
                condition_true = self.int_to_bool(op1.get('val'))
            else:
                condition_true = op1.get('val')
            if condition_true != True and condition_true != False:
                self.error_types('!', op1.elem_type)
            return Element('bool', val = not condition_true)
        
        else:
            op1 = self.__eval_expr(expr.get('op1'))
            op2 = self.__eval_expr(expr.get('op2'))
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
                return Element(op1type, val = op1val + op2val)
            
            elif elem_type == '-' or elem_type == '*' or elem_type == '/':
                dict = {
                    '-': lambda x, y: x - y,
                    '*': lambda x, y: x * y,
                    '/': lambda x, y: x // y
                }
                # only valid -*/ of two non-identical types is int:bool
                if op1type == 'bool' and op2type == 'int':
                    return Element('int', val = dict[elem_type](self.bool_to_int(op1val), op2val))
                if op1type == 'int' and op2type == 'bool':
                    return Element('int', val = dict[elem_type](op1val, self.bool_to_int(op2val)))
                # otherwise, must be only ints
                if op1type != 'int' or op2type != 'int':
                    self.error_types(op1type, op2type)
                return Element('int', val = dict[elem_type](op1val, op2val))
            
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
                    # Comparing two functions

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



    def __run_assignment(self, statement):
        name = statement.get('name')
        expr = statement.get('expression')
        val = self.__eval_expr(expr)
        self.env.set_value(name, val)
        

    def __call_inputi(self, args):
        if len(args) > 1:
            self.error_args('inputi')
        if len(args) == 1:
            prompt = self.__eval_expr(args[0])
            if prompt.elem_type != 'string':
                self.error_args('inputi', 'type')
            super().output(prompt.get('val'))
        #You may assume that only valid integers will be entered in response to an inputi() prompt
        return Element('int', val = int(super().get_input()))


    def __call_inputs(self, args):
        if len(args) > 1:
            self.error_args('inputs')
        if len(args) == 1:
            prompt = self.__eval_expr(args[0])
            if prompt.elem_type != 'string':
                self.error_args('inputs', 'type')
            super().output(prompt.get('val'))
        return Element('string', val = super().get_input())
    

    def __call_print(self, args):
        result = ''
        for arg in args:
            eval_arg = self.__eval_expr(arg).get('val')
            # When you print booleans, the output must be either "true" or "false"
            if eval_arg == True or eval_arg == False:
                eval_arg = str(eval_arg).lower()
            result += str(eval_arg)
        super().output(result)
        # print() function can be called within expressions. The return value of print() should always be nil.
        return Element('nil')

    def __run_function(self, statement):
        name = statement.get('name')
        args = statement.get('args')

        if name == 'inputi':
            return self.__call_inputi(args)
        if name == 'inputs':
            return self.__call_inputs(args)
        if name == 'print':
            return self.__call_print(args)
        
        else:
            func = self.env.get_func(name, len(args))
            if func is None:
                self.error_not_found(name, 'function')
            return self.__call_function(func, args)


    def __call_function(self, func, args):
        params = func.get('args')
        variables, aliases = self.env.get_scope_copy()
        for p, a in zip(params, args):
            name = p.get('name')
            eval_a = self.__eval_expr(a)
            # if param name already an alias, param shadows alias
            if name in aliases:
                del aliases[name]
            # reference arguments: if arg is a variable, it becomes an alias for an existing variable
            if p.elem_type == 'refarg' and eval_a.elem_type == 'var':
                aliases[name] = eval_a.get('name')
            else:
                variables[name] = eval_a
        self.env.add_scope((variables, aliases))
        return_val = self.__run_statements(func.get('statements'))
        self.env.del_scope()
        return return_val

    def __create_lambda(self, expr):
        params = expr.get('args')
        variables, aliases = self.env.get_scope_copy()
        for p in params:
            name = p.get('name')
            if p.elem_type == 'arg':
                variables[name] = name
        

    def __run_if(self, statement):
        condition = self.__eval_expr(statement.get('condition'))
        if condition.elem_type == 'int':
            true = self.int_to_bool(condition.get('val'))
        else:
            true = condition.get('val')
        if true != True and true != False:
            self.error_types('if', condition.elem_type)

        else_statements = statement.get('else_statements')
        self.env.add_scope(self.env.get_scope_copy())
        if true:
            return_val = self.__run_statements(statement.get('statements'))
        elif else_statements:
            return_val = self.__run_statements(else_statements) 
        self.env.del_scope()
        return return_val


    def __run_while(self, statement):
        self.env.add_scope(self.env.get_scope_copy())
        def loop():
            condition = self.__eval_expr(statement.get('condition'))
            if condition.elem_type == 'int':
                true = self.int_to_bool(condition.get('val'))
            else:
                true = condition.get('val')
            if true != True and true != False:
                self.error_types('while', condition.elem_type)
            if true:
                return_val = self.__run_statements(statement.get('statements'))
                if return_val:
                    return return_val
                else:
                    return loop()
        return_val = loop()
        self.env.del_scope()
        return return_val

    
    def __run_return(self, statement):
        return_val = statement.get('expression')
        if return_val is None:
            return Element('nil')
        result = self.__eval_expr(return_val)
        return deepcopy(result)


    def __run_statements(self, statements):
        for s in statements:
            e = s.elem_type
            return_val = None
            if e == '=':
                self.__run_assignment(s)
            if e == 'fcall':
                self.__run_function(s)
            if e == 'if':
                return_val = self.__run_if(s)
            if e == 'while':
                return_val = self.__run_while(s)
            if e == 'return':
                return_val = self.__run_return(s)
            if return_val:
                return return_val
    

    def __init_functions(self, ast):
        for f in ast.get('functions'):
            # this returns False if a duplicate function was attempted to be added
            if not self.env.add_func(f):
                self.error_dup_funcs(f.get('name'))
        # main function must be present
        main = self.env.get_value('main')
        if main is None:
            self.error_not_found('main', 'function')
        return main
    
        
    def run(self, program):
        ast = parse_program(program)
        main = self.__init_functions(ast)
        self.__run_statements(main.get('statements'))


def test():
    inter = Interpreter()
    with open('test.txt') as file:
        prog = file.read()
    inter.run(prog)

test()