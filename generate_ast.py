import ast
from ast import *

class Diff:
    def __init__(self, mod_type, expression1, expression2):
        self.mod_type: str = mod_type        
        self.expression1: stmt = expression1
        self.expression2: stmt = expression2

    def __repr__(self):
        return f'{self.mod_type} on line number {self.expression2.lineno if self.expression2 else self.expression1.lineno}. Expression: {self.expression2}'

    def get_text_between_line_col(self, text: str, expression: stmt):
        expression_text = ''
        line_num = 1
        for line in text.splitlines():
            if line_num < expression.lineno:
                line_num += 1
                continue
            elif line_num > expression.end_lineno:
                break
            elif line_num == expression.lineno and line_num == expression.end_lineno:
                expression_text += line[expression.col_offset:expression.end_col_offset]
            elif line_num == expression.end_lineno:
                expression_text += line[:expression.end_col_offset]
            elif line_num == expression.lineno:
                expression_text += line[expression.col_offset:]            
            else:
                expression_text += line
            line_num += 1
        
        return expression_text

    def print_code(self, file1, file2):
        if self.expression1 != None:
            print(f'{self.mod_type} from line {self.expression1.lineno} of file A: {self.expression1}\n{self.get_text_between_line_col(file1, self.expression1)}')
        elif self.expression2 != None:
            print(f'{self.mod_type} from line {self.expression2.lineno} of file B: {self.expression2}\n{self.get_text_between_line_col(file2, self.expression2)}')


def record_diff(diffs:list[Diff], stmt1: stmt, stmt2: stmt, modification_type: str):
    diffs.append(Diff(modification_type, stmt1, stmt2))

def generate_ast(filepath: str):
    with open(filepath, 'r') as f:
        d = f.read()
    
    tree = ast.parse(d)

    return tree

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
    
    are_equal = True
    i1_cursor = 0
    i2_cursor = 0
    while i1_cursor < len(c1.comparators) and i2_cursor < len(c2.comparators):
        cmp1 = c1.comparators[i1_cursor]
        cmp2 = c2.comparators[i2_cursor]

        if not node_equality(cmp1, cmp2):
            are_equal = False
        
        o1 = c1.ops[i1_cursor]
        o2 = c2.ops[i2_cursor]

        if type(o1) != type(o2):
            are_equal = False
            
        i1_cursor += 1
        i2_cursor += 1

    if any(c1.comparators[i1_cursor:]):
        are_equal = False
    if any(c2.comparators[i2_cursor:]):
        are_equal = False

    return are_equal

# flatten nodes for LCS
# unpack things we should consider separately
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
            flattened.extend(flatten_ast_with_structure(node.body))
    
    return flattened

# comparison of nodes used for LCS
# compare the items that affect everything about that statement - like for If, if the test changes, we say the whole statement has changed
def node_equality(node1: stmt, node2: stmt):
    if type(node1) != type(node2):
        return False
    
    if isinstance(node1, (BoolOp, While, For)):
        return True  # We flattened these, so just a type check is good
    elif isinstance(node1, If):
        return node_equality(node1.test, node2.test)
    elif isinstance(node1, Name):
        return node1.id == node2.id
    elif isinstance(node1, Constant):
        return node1.value == node2.value
    elif isinstance(node1, Compare):
        return compare_Compare(node1, node2)
    elif isinstance(node1, Return):
        return node_equality(node1.value, node2.value)
    elif isinstance(node1, Assign):
        return node_equality(node1.targets[0], node2.targets[0]) and node_equality(node1.value, node2.value)
    elif isinstance(node1, BinOp):
        return node_equality(node1.left, node2.left) and node_equality(node1.right, node2.right) and node_equality(node1.op, node2.op)
    else:
        return True  # Default to True for other node types

# like typical LCS but instead of checking for regular ==, we use node_equality
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
    lcs_result = set()
    i, j = m, n
    while i > 0 and j > 0:
        if node_equality(X[i-1], Y[j-1]):
            # we append the nodes from both trees so we can just check the objects directly later
            lcs_result.add((X[i-1], Y[j-1]))
            i -= 1
            j -= 1
        elif L[i-1][j] > L[i][j-1]:
            i -= 1
        else:
            j -= 1

    # if we care about order, make lcs_result a list and reverse it.
    # return list(reversed(lcs_result))
    return lcs_result

# AST diff
def compare_stmtlist_lcs(slist1: list[stmt], slist2: list[stmt], diffs: list[Diff]):
    flat1 = flatten_ast_with_structure(slist1)
    flat2 = flatten_ast_with_structure(slist2)
    
    print(f'flat1: {flat1}')
    print(f'flat2: {flat2}')
    lcs_result = lcs_flattened(flat1, flat2)

    print(f'lcs: {lcs_result}')

    # here we can just take advantage 
    # we ignore missing BoolOps because they are just containers
    for statement in flat1:
        if type(statement) not in [BoolOp] and statement not in [x[0] for x in lcs_result]:
            record_diff(diffs, statement, None, 'deletion')
            
    for statement in flat2:
        if statement not in [x[1] for x in lcs_result] and not isinstance(statement, BoolOp):
            record_diff(diffs, None, statement, 'addition')
    
    return len(diffs) == 0

def main():
    # test_file_A = 'simple_method_A.py'
    # test_file_B = 'simple_method_B.py'
    test_file_A = 'two_ifs_A.py'
    test_file_B = 'two_ifs_B.py'

    t1 = generate_ast(test_file_A)
    t2 = generate_ast(test_file_B)

    f1 = t1.body[0]
    f2 = t2.body[0]

    diffs = []
    match = compare_stmtlist_lcs(f1.body, f2.body, diffs)
    print(f'Match? {match}')
    
    file1 = open(test_file_A).read()
    file2 = open(test_file_B).read()
    for d in diffs:
        d.print_code(file1, file2)

if __name__ == '__main__':
    main()