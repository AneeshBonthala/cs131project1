from brewparse import parse_program
from intbase import InterpreterBase

class Interpreter(InterpreterBase):

    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)

    # for testing purposes
    def print(self, program):
        ast = parse_program(program)
        return ast.dict['functions'][0].dict['statements']

    def run_statement(self, statement):
        pass

    def run(self, program):
        self.variables = {}
        ast = parse_program(program)
        main_node = ast.dict['functions'][0]
        for statement in main_node.dict['statements']:
            self.run_statement(statement)







    

inter = Interpreter()
with open('test.txt') as test:
    prog = test.read()

with open('test.txt', 'a') as test:
    test.write('\n')
    test.write(str(inter.print(prog)))
