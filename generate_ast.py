import ast
from ast import *

def generate_ast(filepath: str):
    with open(filepath, 'r') as f:
        d = f.read()
    
    tree = ast.parse(d)

    return tree

def compare_BinOp(op1: BinOp, op2: BinOp):
    if op1.op != op2.op:
        return False
    
    if op1.left.id != op2.left.id:
        return False
    
    return compare_stmt(op1.right, op2.right)

def compare_Constant(c1: Constant, c2:Constant):
    return c1.value == c2.value

def compare_assigns(a1: Assign, a2: Assign):
    target1 = a1.targets[0].id
    target2 = a2.targets[0].id

    if target1 != target2:
        return False
    
    return compare_stmt(a1.value, a2.value)

def compare_value(c1, c2):
    if type(c1) != type(c2):
        return False

    c1_type = type(c1)

    if c1_type == Constant:
        return c1.value == c2.value
    elif c1_type == Name: # probably doesn't belong here as this is not a value but o well
        return c1.id == c2.id    
    else:
        raise Exception(f'Unknown value type: {type(c1)} on line {c1.lineno}')

def compare_Return(r1: Return, r2: Return):
    return compare_stmt(r1.value, r2.value)

def compare_Compare(c1: Compare, c2: Compare):
    left1 = c1.left.id
    left2 = c2.left.id

    if left1 != left2:
        return False
    
    if len(c1.comparators) != len(c2.comparators):
        return False

    if len(c1.ops) != len(c2.ops):
        return False
    
    if len(c1.comparators) != len(c1.ops):
        raise Exception(f'Unknown if construct. comparators: {c1.comparators} and ops: {c1.ops}')
    
    i1_cursor = 0
    i2_cursor = 0
    while i1_cursor < len(c1.comparators) and i2_cursor < len(c2.comparators):
        cmp1 = c1.comparators[i1_cursor]
        cmp2 = c2.comparators[i2_cursor]

        if not compare_value(cmp1, cmp2):
            return False
        
        o1 = c1.ops[i1_cursor]
        o2 = c2.ops[i2_cursor]

        if type(o1) != type(o2):
            print(f'Mismatched IF operatror types: {type(o1)} and {type(o2)}')
            return False
            
        i1_cursor += 1
        i2_cursor += 1

    return i1_cursor == len(c1.comparators) and i2_cursor == len(c2.comparators)


def compare_If(i1: If, i2: If):
    if not compare_stmt(i1.test, i2.test):
        return False
    
    return compare_stmtlist(i1.body, i2.body)
        
def compare_BoolOp(b1: BoolOp, b2: BoolOp):
    if type(b1.op) != type(b2.op):
        return False
    
    return compare_stmtlist(b1.values, b2.values)

def compare_stmt(stmt1: stmt, stmt2: stmt):
    if type(stmt1) != type(stmt2):
        return False
    
    expression_type = type(stmt1)
    
    if expression_type == BinOp:
        return compare_BinOp(stmt1, stmt2)
    elif expression_type == Constant:
        return compare_Constant(stmt1, stmt2)
    elif expression_type == Assign:
        return compare_assigns(stmt1, stmt2)
    elif expression_type == If:
        return compare_If(stmt1, stmt2)
    elif expression_type == Return:
        return compare_Return(stmt1, stmt2)
    elif expression_type == Name:
        return compare_value(stmt1, stmt2)
    elif expression_type == Compare:
        return compare_Compare(stmt1, stmt2)
    elif expression_type == BoolOp:
        return compare_BoolOp(stmt1, stmt2)
    else:
        print(f'Unknown expression type: {type(stmt1)} on line {stmt1.lineno} with dir: {dir(stmt1)}')
        raise Exception("unknown expression type")

class Diff:
    def __init__(self, mod_type, lineno, expression):
        self.mod_type: str = mod_type
        self.lineno: int = lineno
        self.expression: stmt = expression

    def __repr__(self):
        return f'{self.mod_type} on line number {self.lineno}. Expression: {self.expression}'

diffs = []
def compare_stmtlist(slist1: list[stmt], slist2: list[stmt], f1_cursor = 0, f2_cursor = 0, actual_comparison = True):
    equals = True
    while f1_cursor < len(slist1) and f2_cursor < len(slist2):
        stmt1 = slist1[f1_cursor]
        stmt2 = slist2[f2_cursor]

        if not compare_stmt(stmt1, stmt2):
            print(f'Statements differ. A line: {stmt1.lineno} B line: {stmt2.lineno}')

            # check to see if this diff is an addition or removal. this only works for immediate neighbors.
            # need to rework this alg to find LCS instead.
            if actual_comparison and compare_stmtlist(slist1, slist2, f1_cursor, f2_cursor + 1, False):
                diffs.append(Diff('addition', stmt2.lineno, stmt2))
                f2_cursor += 1
            elif actual_comparison and compare_stmtlist(slist1, slist2, f1_cursor + 1, f2_cursor, False):
                diffs.append(Diff('removal', stmt2.lineno, stmt2))
                f1_cursor += 1
            
            equals = equals and False

        f1_cursor += 1
        f2_cursor += 1
    
    if actual_comparison:
        if len(slist1) < len(slist2):
            for stmt in slist2[f2_cursor:]:
                diffs.append(Diff('addition', stmt.lineno, stmt))
        elif len(slist1) > len(slist2):
            for stmt in slist1[f1_cursor:]:
                diffs.append(Diff('removal', stmt.lineno, stmt))
    
    return equals

def main():
    t1 = generate_ast('simple_method_A.py')
    t2 = generate_ast('simple_method_B.py')

    f1 = t1.body[0]
    f2 = t2.body[0]

    match = compare_stmtlist(f1.body, f2.body)
    print(match)
    print(diffs)

if __name__ == '__main__':
    main()