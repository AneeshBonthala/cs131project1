from brewparse import parse_program
from intbase import InterpreterBase

class Interpreter(InterpreterBase):

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)

    # for testing purposes
    def print(self, program):
        ast = parse_program(program)
        return ast

    def eval_expr(self, expr):
        if expr.elem_type == 'int' or expr.elem_type == 'string':
            return expr.dict['val']
        elif expr.elem_type == 'var':
            return self.variables[expr.dict['name']]
        elif expr.elem_type == '+':
            return self.eval_expr(expr.dict['op1']) + self.eval_expr(expr.dict['op2'])
        elif expr.elem_type == '-':
            return self.eval_expr(expr.dict['op1']) - self.eval_expr(expr.dict['op2'])

    def run_assignment(self, statement):
        self.variables[statement.dict['name']] = self.eval_expr(statement.dict['expression'])
        print(self.variables)

    def run_function(statement):
        pass

    def run_statement(self, statement):
        if statement.elem_type == '=':
            self.run_assignment(statement)
        elif statement.elem_type == 'fcall':
            self.run_function(statement)

    def run(self, program):
        self.variables = {}
        ast = parse_program(program)
        main_node = ast.dict['functions'][0]
        for statement in main_node.dict['statements']:
            self.run_statement(statement)





    
def test():
    inter = Interpreter()
    with open('test.txt') as test:
        prog = test.read()

    with open('test.txt', 'a') as test:
        test.write('\n')
        test.write(str(inter.run(prog)))

test()
