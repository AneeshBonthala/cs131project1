from brewparse import parse_program
from intbase import InterpreterBase, ErrorType
from element import Element
from copy import deepcopy, copy

class Environment:
    def __init__(self):
        self.env = [{}]

    def get(self, symbol):
        for e in reversed(self.env):
            if symbol in e:
                return e[symbol]
        return None
    
    def set(self, symbol, value, type):
        for e in reversed(self.env):
            if symbol in e:
                e[symbol].set_value(value)
                e[symbol].set_type(type)
                return
        self.env[-1][symbol] = Value(type, value)

    def create(self, symbol, box):
        self.env[-1][symbol] = box

    def push(self):
        self.env.append({})

    def push_closure(self, closure):
        self.env.append(closure)

    def pop(self):
        self.env.pop()

class Value:
    def __init__(self, type, value):
        self.t = type
        self.v = value

    def value(self):
        return self.v
    
    def set_value(self, value):
        self.v = value
    
    def type(self):
        return self.t
    
    def set_type(self, type):
        self.t = type

class Lambda:
    def __init__(self, env, func):
        closure = {}
        for scope in env:
            closure.update(scope)
        self.closure = closure
        self.func = func



class Interpreter(InterpreterBase):

    def __to_bool(self, val):
        if isinstance(val, int):
            return False if val == 0 else True
        if isinstance(val, bool):
            return val
        return None

    def __to_int(self, val):
        if isinstance(val, bool):
            return 1 if val else 0
        if isinstance(val, int):
            return val
        return None

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.env = Environment()

    def run(self, program):
        ast = parse_program(program)
        main = self.__init_functions(ast)
        self.__run_statements(main.get('statements'))

    def __init_functions(self, ast):
        self.functions = {}
        for func in ast.get('functions'):
            func_name = func.get('name')
            num_args = len(func.get('args'))
            if func_name in self.functions:
                if num_args in self.functions[func_name]:
                    super().error(ErrorType.NAME_ERROR, f"Duplicate functions for {func_name} are not allowed.") 
            else:
                self.functions[func_name] = {}
            self.functions[func_name][num_args] = func
        if 'main' not in self.functions:
            super().error(ErrorType.NAME_ERROR, "Main function was not found.")
        if len(self.functions['main'].keys()) > 1:
            super().error(ErrorType.NAME_ERROR, "Cannot overload main function.")
        if 0 not in self.functions['main']:
            super().error(ErrorType.NAME_ERROR, "Main function may not take >0 arguments.")
        return self.functions['main'][0]
    
    def __get_function(self, func_name, num_args):
        if func_name not in self.functions:
            super().error(ErrorType.NAME_ERROR, f"Function {func_name} was not found.")
        if num_args not in self.functions[func_name]:
            super().error(ErrorType.NAME_ERROR, f"Function {func_name} taking {num_args} arguments was not found.")
        return self.functions[func_name][num_args]
    
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

    def __run_assignment(self, statement):
        symbol = statement.get('name')
        expr = statement.get('expression')
        val = self.__eval_expr(expr)
        self.env.set(symbol, val.value(), val.type())


    def __run_function(self, statement):
        name = statement.get('name')
        args = statement.get('args')
        num_args = len(args)

        if name == 'inputi':
            return self.__call_inputi(args)
        if name == 'inputs':
            return self.__call_inputs(args)
        if name == 'print':
            return self.__call_print(args)
        
        alias = self.env.get(name)
        if alias:
            if alias.type() == 'func':
                name = alias.value().get('name')
                num_args = len(alias.value().get('args'))
            elif alias.type() == 'lambda':
                return self.__run_lambda(alias, args)
            else:
                super().error(ErrorType.TYPE_ERROR, f"Variable is not callable.")

        func = self.__get_function(name, num_args)
        params = func.get('args')
        if len(params) != len(args):
            super().error(ErrorType.TYPE_ERROR, f"Invalid number of arguments provided to function.")
        self.env.push()
        for p, a in zip(params, args):
            param_name = p.get('name')
            if p.elem_type == 'refarg' and a.elem_type == 'var':
                arg_val = self.__eval_expr(a)
            else:
                arg_val = deepcopy(self.__eval_expr(a))
            self.env.create(param_name, arg_val)
        return_val = self.__run_statements(func.get('statements'))
        self.env.pop()
        return return_val if return_val is not None else Value('nil', None)
    
    def __run_lambda(self, lambda_func, args):
        closure = lambda_func.value().closure
        func = lambda_func.value().func
        params = func.get('args')
        if len(params) != len(args):
            super().error(ErrorType.TYPE_ERROR, f"Invalid number of arguments provided to lambda function.")
        for p, a in zip(params, args):
            param_name = p.get('name')
            if p.elem_type == 'refarg' and a.elem_type == 'var':
                arg_val = self.__eval_expr(a)
            else:
                arg_val = deepcopy(self.__eval_expr(a))
            closure[param_name] = arg_val
        self.env.push_closure(closure)
        return_val = self.__run_statements(func.get('statements'))
        self.env.pop()
        return return_val if return_val is not None else Value('nil', None)
    
    def __eval_expr(self, expr):
        elem_type = expr.elem_type
        
        if elem_type == 'fcall':
            return self.__run_function(expr)
        
        if elem_type == 'nil':
            return Value('nil', None)
        if elem_type == 'bool':
            return Value('nil', expr.get('val'))
        if elem_type == 'int':
            return Value('int', expr.get('val'))
        if elem_type == 'string':
            return Value('string', expr.get('val'))
        
        if elem_type == 'var':
            var_name = expr.get('name')
            if var_name in self.functions:
                if len(self.functions[var_name].keys()) > 1:
                    super().error(ErrorType.NAME_ERROR, "Cannot return or assign overloaded function name.")
                return Value('func', list(self.functions[var_name].values())[0])
            val = self.env.get(var_name)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} was not found.")
            return val
        
        if elem_type == 'lambda':
            return Value('lambda', Lambda(deepcopy(self.env.env), expr))

        if elem_type == 'neg' or elem_type == '!':
            op1 = self.__eval_expr(expr.get('op1'))
            return self.__unary_ops(elem_type, op1.value(), op1.type())
        
        else:
            op1 = self.__eval_expr(expr.get('op1'))
            op2 = self.__eval_expr(expr.get('op2'))
            return self.__binary_ops(elem_type, op1.value(), op1.type(), op2.value(), op2.type())
        

    def __run_if(self, statement):
        condition = self.__eval_expr(statement.get('condition')).value()
        condition = self.__to_bool(condition)
        if condition is None:
            super().error(ErrorType.TYPE_ERROR, "Incorrect condition type for 'if' statement.")
        else_statements = statement.get('else_statements')
        self.env.push()
        return_val = None
        if condition:
            return_val = self.__run_statements(statement.get('statements'))
        elif else_statements:
            return_val = self.__run_statements(else_statements) 
        self.env.pop()
        return return_val
    
    def __run_while(self, statement):
        condition = self.__eval_expr(statement.get('condition')).value()
        condition = self.__to_bool(condition)
        if condition is None:
            super().error(ErrorType.TYPE_ERROR, "Incorrect condition type for 'while' statement.")
        return_val = None
        if condition:
            self.env.push()
            return_val = self.__run_statements(statement.get('statements'))
            if return_val:
                self.env.pop()
                return return_val
            self.env.pop()
            self.__run_while(statement)
        return return_val

    def __run_return(self, statement):
        return_val = statement.get('expression')
        if return_val is None:
            return Value('nil', None)
        result = self.__eval_expr(return_val)
        return deepcopy(result)


    ############################# HELPER FUNCTIONS

    def __unary_ops(self, op, opval, optype):
        if op == 'neg':
            if optype != 'int':
                super().error(ErrorType.TYPE_ERROR, f"Non-integer value cannot be negated with '-'.")
            return Value('int', -1 * opval)
        # op == '!':
        opval = self.__to_bool(opval)
        if opval is None:
            super().error(ErrorType.TYPE_ERROR, f"Non-integer or non-boolean value cannot be negated with '!'.")
        return Value('bool', not opval)


    def __binary_ops(self, op, op1val, op1type, op2val, op2type):
        if op == '+':
            if op1type == 'string' and op2type == 'string':
                return Value('string', op1val + op2val)
            op1val = self.__to_int(op1val)
            op2val = self.__to_int(op2val)
            if op1val is None or op2val is None:
                super().error(ErrorType.TYPE_ERROR, f"Incompatible types for '+' operation.")
            return Value('int', op1val + op2val)
        if op == '-' or op == '*' or op == '/':
            op1val = self.__to_int(op1val)
            op2val = self.__to_int(op2val)
            if op1val is None or op2val is None:
                super().error(ErrorType.TYPE_ERROR, f"Incompatible types for '{op}' operation.")
            dict = {
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x // y,
            }
            return Value('int', dict[op](op1val, op2val))
        if op == '==':
            if op1type == op2type:
                return Value('bool', op1val == op2val)
            op1val = self.__to_bool(op1val)
            op2val = self.__to_bool(op2val)
            if op1val is None or op2val is None:
                return Value('bool', False)
            return Value('bool', op1val == op2val)
        if op == '!=':
            if op1type == op2type:
                return Value('bool', op1val != op2val)
            op1val = self.__to_bool(op1val)
            op2val = self.__to_bool(op2val)
            if op1val is None or op2val is None:
                return Value('bool', True)
            return Value('bool', op1val != op2val)
        if op == '||' or op == '&&':
            op1val = self.__to_bool(op1val)
            op2val = self.__to_bool(op2val)
            if op1val is None or op2val is None:
                super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {op} operation.")
            dict = {
                '||': lambda x, y: x or y,
                '&&': lambda x, y: x and y
            }
            return Value('bool', dict[op](op1val, op2val))
        # comparison operators
        if op1type != 'int' or op2type != 'int':
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types for '{op}' operation.")
        dict = {
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
        }
        return Value('bool', dict[op](op1val, op2val))
            
    def __call_inputi(self, args):
        if len(args) > 1:
            super().error(ErrorType.NAME_ERROR, "Invalid number of arguments provided for 'inputi' function.")
        if len(args) == 1:
            prompt = self.__eval_expr(args[0])
            if prompt.type() != 'string':
                super().error(ErrorType.TYPE_ERROR, "Invalid argument type provided for 'inputi' function.")
            super().output(prompt.value())
        return Value('int', int(super().get_input()))

    def __call_inputs(self, args):
        if len(args) > 1:
            super().error(ErrorType.NAME_ERROR, "Invalid number of arguments provided for 'inputs' function.")
        if len(args) == 1:
            prompt = self.__eval_expr(args[0])
            if prompt.type() != 'string':
                super().error(ErrorType.TYPE_ERROR, "Invalid argument type provided for 'inputs' function.")
            super().output(prompt.value())
        return Value('string', super().get_input())
    
    def __call_print(self, args):
        result = ''
        for arg in args:
            msg = self.__eval_expr(arg).value()
            if msg == True or msg == False:
                msg = str(msg).lower()
            result += str(msg)
        super().output(result)
        return Value('nil', None)

            
            


def test():
    inter = Interpreter()
    with open('test.txt') as file:
        prog = file.read()
    inter.run(prog)

test()