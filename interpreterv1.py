from brewparse import parse_program
from intbase import InterpreterBase

class Interpreter(InterpreterBase):

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.variables = {}

    # for testing purposes
    def print(self, program):
        ast = parse_program(program)
        return ast

    def eval_expr(self, expr):
        if expr.elem_type == 'int' or expr.elem_type == 'string':
            return expr.get('val')
        elif expr.elem_type == 'var':
            return self.variables[expr.get('name')]
        elif expr.elem_type == '+':
            return self.eval_expr(expr.get('op1')) + self.eval_expr(expr.get('op2'))
        elif expr.elem_type == '-':
            return self.eval_expr(expr.get('op1')) - self.eval_expr(expr.get('op2'))
        elif expr.elem_type == 'fcall':
            return self.run_function(expr)

    def run_assignment(self, statement):
        self.variables[statement.get('name')] = self.eval_expr(statement.get('expression'))

    def run_function(self, statement):
        args = statement.get('args')
        if statement.get('name') == 'inputi':
            # handle incorrect # or type of args error
            super().output(args[0])
            return super().get_input()
        elif statement.get('name') == 'print':
            # handle incorrect # or type of args error
            super().output(args[0])

    def run_statement(self, statement):
        if statement.elem_type == '=':
            self.run_assignment(statement)
        elif statement.elem_type == 'fcall':
            self.run_function(statement)

    def run(self, program):
        ast = parse_program(program)
        main_node = ast.get('functions')[0]
        for statement in main_node.get('statements'):
            self.run_statement(statement)





    
def test():
    inter = Interpreter()
    with open('test.txt') as test:
        prog = test.read()

    with open('test.txt', 'a') as test:
        test.write('\n')
        test.write(str(inter.run(prog)))

test()
