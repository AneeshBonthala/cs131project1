from brewparse import parse_program
from intbase import InterpreterBase, ErrorType

class Interpreter(InterpreterBase):


    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.variables = {}


    def eval_expr(self, expr):

        if expr.elem_type == 'int' or expr.elem_type == 'string':
            return expr.get('val')
        
        if expr.elem_type == 'var':
            var = expr.get('name')
            if var == None: super().error(ErrorType.NAME_ERROR, 'Variable has not been defined.')
            return self.variables[var]
        
        if expr.elem_type == '+':
            try: result = self.eval_expr(expr.get('op1')) + self.eval_expr(expr.get('op2'))
            except TypeError: super().error(ErrorType.TYPE_ERROR, 'Incompatible types for arithmetic operation.')
            else: return result
        
        if expr.elem_type == '-':
            try: result = self.eval_expr(expr.get('op1')) - self.eval_expr(expr.get('op2'))
            except TypeError: super().error(ErrorType.TYPE_ERROR, 'Incompatible types for arithmetic operation.')
            else: return result
        
        if expr.elem_type == 'fcall':
            return self.run_function(expr)
        

    def run_assignment(self, statement):
        self.variables[statement.get('name')] = self.eval_expr(statement.get('expression'))


    def run_function(self, statement):
        args = statement.get('args')

        if statement.get('name') == 'inputi':
            if len(args) > 1: super().error(ErrorType.NAME_ERROR, 'Invalid number of parameters provided.')
            if len(args) == 1: super().output(self.eval_expr(args[0]))
            return int(super().get_input())
        
        if statement.get('name') == 'print':
            result = ''
            for arg in args:
                eval_arg = self.eval_expr(arg)
                result += str(eval_arg)
            super().output(result)


    def run_statement(self, statement):

        if statement.elem_type == '=':
            self.run_assignment(statement)

        elif statement.elem_type == 'fcall':
            self.run_function(statement)


    def run(self, program):
        ast = parse_program(program)

        main_node = None
        for func in ast.get('functions'):
            if func.get('name') == 'main': main_node = func
        if not main_node: super().error(ErrorType.NAME_ERROR, "No main function was found.")

        for statement in main_node.get('statements'):
            self.run_statement(statement)


# def test():
#     inter = Interpreter()
#     with open('test.txt') as file:
#         prog = file.read()
#     inter.run(prog)

# test()