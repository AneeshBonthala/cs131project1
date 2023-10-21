from brewparse import parse_program
from intbase import InterpreterBase, ErrorType

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

        if elem_type == 'int' or elem_type == 'string':
            return expr.get('val')
        
        if elem_type == 'var':
            var = expr.get('name')
            if var not in self.variables.keys(): self.error_not_found(var)
            return self.variables[var]
        
        if expr.elem_type == 'fcall':
            return self.run_function(expr)
        
        else:
            op_dict = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y
            }
            try:
                op1 = self.eval_expr(expr.get('op1'))
                op2 = self.eval_expr(expr.get('op2'))
                result = op_dict[elem_type](op1, op2)
            except TypeError: self.error_types(type(op1), type(op2))
            else: return result
        

    def run_assignment(self, statement):
        self.variables[statement.get('name')] = self.eval_expr(statement.get('expression'))


    def run_function(self, statement):
        args = statement.get('args')
        name = statement.get('name')

        if name == 'inputi':
            if len(args) > 1: self.error_args('inputi')
            if len(args) == 1:
                prompt = self.eval_expr(args[0])
                if not isinstance(prompt, str): self.error_args('inputi', 'type')
                super().output(prompt)
            return int(super().get_input())
        
        if name == 'print':
            result = ''
            for arg in args:
                eval_arg = self.eval_expr(arg)
                result += str(eval_arg)
            super().output(result)

        else: self.error_not_found(name, 'function')


    def run_statement(self, statement):
        elem_type = statement.elem_type

        if elem_type == '=':
            self.run_assignment(statement)

        elif elem_type == 'fcall':
            self.run_function(statement)


    def run(self, program):
        ast = parse_program(program)

        main_node = None
        for func in ast.get('functions'):
            if func.get('name') == 'main': main_node = func
        if not main_node: self.error_not_found('main', 'function')

        for statement in main_node.get('statements'):
            self.run_statement(statement)


# def test():
#     inter = Interpreter()
#     with open('test.txt') as file:
#         prog = file.read()
#     inter.run(prog)

# test()