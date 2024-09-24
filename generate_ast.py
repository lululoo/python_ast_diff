import ast
from ast import *

class Diff:
    def __init__(self, mod_type, expression1, expression2):
        self.mod_type: str = mod_type        
        self.expression1: stmt = expression1
        self.expression2: stmt = expression2

    def __repr__(self):
        return f'{self.mod_type} on line number {self.expression2.lineno if self.expression2 else self.expression1.lineno}. Expression: {self.expression2}'

def record_diff(diffs:list[Diff], stmt1: stmt, stmt2: stmt, modification_type: str):
    diffs.append(Diff(modification_type, stmt1, stmt2))

def generate_ast(filepath: str):
    with open(filepath, 'r') as f:
        d = f.read()
    
    tree = ast.parse(d)

    return tree

def compare_BinOp(op1: BinOp, op2: BinOp, diffs: list[Diff]):
    if op1.op != op2.op:
        record_diff(diffs, op1, op2, '')
        return False
    
    if op1.left.id != op2.left.id:
        record_diff(diffs, op1, op2, '')
        return False
    
    return compare_stmt(op1.right, op2.right, diffs)

def compare_Constant(c1: Constant, c2:Constant, diffs: list[Diff]):
    if c1.value != c2.value:
        record_diff(diffs, c1, c2, '')
        return False
    return True

def compare_assigns(a1: Assign, a2: Assign, diffs: list[Diff]):
    target1 = a1.targets[0].id
    target2 = a2.targets[0].id

    if target1 != target2:
        record_diff(diffs, a1, a2, '')
        return False
    
    return compare_stmt(a1.value, a2.value, diffs)

def compare_value(c1, c2, diffs: list[Diff]):
    if type(c1) != type(c2):
        record_diff(diffs, c1, c2, '')
        return False

    c1_type = type(c1)

    if c1_type == Constant:
        are_equal = c1.value == c2.value
    elif c1_type == Name: # probably doesn't belong here as this is not a value but o well
        are_equal = c1.id == c2.id
    else:
        raise Exception(f'Unknown value type: {type(c1)} on line {c1.lineno}')
    
    if not are_equal:
        record_diff(diffs, c1, c2, '')

    return are_equal

def compare_Return(r1: Return, r2: Return, diffs: list[Diff]):
    return compare_stmt(r1.value, r2.value, diffs)

def compare_Compare(c1: Compare, c2: Compare, diffs: list[Diff]):
    left1 = c1.left.id
    left2 = c2.left.id

    if left1 != left2:
        record_diff(diffs, c1, c2, '')
        return False
    
    if len(c1.comparators) != len(c2.comparators):
        record_diff(diffs, c1, c2, '')
        return False

    if len(c1.ops) != len(c2.ops):
        record_diff(diffs, c1, c2, '')
        return False
    
    if len(c1.comparators) != len(c1.ops):
        raise Exception(f'Unknown if construct. comparators: {c1.comparators} and ops: {c1.ops}')
    
    are_equal = True
    i1_cursor = 0
    i2_cursor = 0
    while i1_cursor < len(c1.comparators) and i2_cursor < len(c2.comparators):
        cmp1 = c1.comparators[i1_cursor]
        cmp2 = c2.comparators[i2_cursor]

        if not compare_value(cmp1, cmp2, diffs):
            are_equal = False
        
        o1 = c1.ops[i1_cursor]
        o2 = c2.ops[i2_cursor]

        if type(o1) != type(o2):
            record_diff(diffs, c1, c2, '')
            are_equal = False
            
        i1_cursor += 1
        i2_cursor += 1

    for comparator in c1.comparators[i1_cursor:]:
        are_equal = False
        record_diff(diffs, comparator, None, 'deletion')
    for comparator in c2.comparators[i2_cursor:]:
        are_equal = False
        record_diff(diffs, None, comparator, 'addition')

    return are_equal


def compare_If(i1: If, i2: If, diffs: list[Diff]):
    if not compare_stmt(i1.test, i2.test, diffs):
        return False
    
    return compare_stmtlist(i1.body, i2.body, diffs)
        
def compare_BoolOp(b1: BoolOp, b2: BoolOp, diffs: list[Diff]):
    if type(b1.op) != type(b2.op):
        record_diff(diffs, b1, b2, '')
        return False
    
    return compare_stmtlist(b1.values, b2.values, diffs)

def compare_stmt(stmt1: stmt, stmt2: stmt, diffs: list[Diff]):
    if type(stmt1) != type(stmt2):
        record_diff(diffs, stmt1, stmt2, '')
        return False
    
    expression_type = type(stmt1)
    
    if expression_type == BinOp:
        return compare_BinOp(stmt1, stmt2, diffs)
    elif expression_type == Constant:
        return compare_Constant(stmt1, stmt2, diffs)
    elif expression_type == Assign:
        return compare_assigns(stmt1, stmt2, diffs)
    elif expression_type == If:
        return compare_If(stmt1, stmt2, diffs)
    elif expression_type == Return:
        return compare_Return(stmt1, stmt2, diffs)
    elif expression_type == Name:
        return compare_value(stmt1, stmt2, diffs)
    elif expression_type == Compare:
        return compare_Compare(stmt1, stmt2, diffs)
    elif expression_type == BoolOp:
        return compare_BoolOp(stmt1, stmt2, diffs)
    else:
        print(f'Unknown expression type: {type(stmt1)} on line {stmt1.lineno} with dir: {dir(stmt1)}')
        raise Exception("unknown expression type")
    
def flatten_ast_with_structure(node):
    flattened = []
    
    if isinstance(node, list):
        for item in node:
            flattened.extend(flatten_ast_with_structure(item))
    elif isinstance(node, AST):
        flattened.append(node)        
        if isinstance(node, BoolOp):            
            flattened.extend(flatten_ast_with_structure(node.values))
        elif isinstance(node, If):
            flattened.extend(flatten_ast_with_structure(node.test))
            flattened.extend(flatten_ast_with_structure(node.body))
    
    return flattened

def node_equality(node1, node2):
    if type(node1) != type(node2):
        return False
    
    if isinstance(node1, (BoolOp, If, While, For)):
        return True  # We'll compare these in detail later
    elif isinstance(node1, Name):
        return node1.id == node2.id
    elif isinstance(node1, Constant):
        return node1.value == node2.value
    elif isinstance(node1, BinOp):
        return type(node1.op) == type(node2.op)
    elif isinstance(node1, Compare):
        return type(node1.ops[0]) == type(node2.ops[0])
    else:
        return True  # Default to True for other node types

def lcs_flattened(X, Y):
    m = len(X)
    n = len(Y)
    L = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if node_equality(X[i-1], Y[j-1]):
                L[i][j] = L[i-1][j-1] + 1
            else:
                L[i][j] = max(L[i-1][j], L[i][j-1])

    # Backtrack to find the LCS
    lcs_result = []
    i, j = m, n
    while i > 0 and j > 0:
        if node_equality(X[i-1], Y[j-1]):
            lcs_result.append(X[i-1])
            i -= 1
            j -= 1
        elif L[i-1][j] > L[i][j-1]:
            i -= 1
        else:
            j -= 1

    return list(reversed(lcs_result))

def compare_stmtlist(slist1: list[stmt], slist2: list[stmt], diffs: list[Diff]):
    flat1 = flatten_ast_with_structure(slist1)
    flat2 = flatten_ast_with_structure(slist2)
    
    lcs_result = lcs_flattened(flat1, flat2)
    
    i, j, k = 0, 0, 0
    while i < len(flat1) or j < len(flat2):
        if k < len(lcs_result) and node_equality(flat1[i], lcs_result[k]):
            if node_equality(flat2[j], lcs_result[k]):
                # Nodes match, perform detailed comparison
                compare_nodes(flat1[i], flat2[j], diffs)
                i += 1
                j += 1
                k += 1
            else:
                # Node added in flat2
                record_diff(diffs, None, flat2[j], 'addition')
                j += 1
        elif k < len(lcs_result) and node_equality(flat2[j], lcs_result[k]):
            # Node removed from flat1
            record_diff(diffs, flat1[i], None, 'deletion')
            i += 1
        else:
            if i < len(flat1) and j < len(flat2):
                record_diff(diffs, flat1[i], flat2[j], 'modification')
            elif i < len(flat1):
                record_diff(diffs, flat1[i], None, 'deletion')
            elif j < len(flat2):
                record_diff(diffs, None, flat2[j], 'addition')
            
            i += 1
            j += 1

    return len(diffs) == 0

def compare_nodes(node1: stmt, node2: stmt, diffs: list[Diff]):
    if isinstance(node1, BoolOp) and isinstance(node2, BoolOp):
        compare_BoolOp(node1, node2, diffs)
    elif isinstance(node1, If) and isinstance(node2, If):
        compare_If(node1, node2, diffs)
    elif isinstance(node1, (While, For)) and isinstance(node2, (While, For)):
        raise Exception("No support for while, for yet")
    else:
        compare_stmt(node1, node2, diffs)

def main():
    t1 = generate_ast('simple_method_A.py')
    t2 = generate_ast('simple_method_B.py')

    f1 = t1.body[0]
    f2 = t2.body[0]

    diffs = []
    match = compare_stmtlist(f1.body, f2.body, diffs)
    print(match)
    print(diffs)

if __name__ == '__main__':
    main()