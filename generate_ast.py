import ast
from ast import *

class Diff:
    def __init__(self, mod_type, expression1, expression2):
        self.mod_type: str = mod_type        
        self.expression1: stmt = expression1
        self.expression2: stmt = expression2

    def __repr__(self):
        return f'{self.mod_type} on line number {self.expression2.lineno if self.expression2 else self.expression1.lineno}. Expression: {self.expression2}'

    def get_text_between_line_col(self, text: str, lineno, col_offset, end_lineno, end_col_offset):
        expression_text = ''
        line_num = 1
        for line in text.splitlines():
            if line_num < lineno:
                line_num += 1
                continue
            elif line_num > end_lineno:
                break
            elif line_num == lineno and line_num == end_lineno:
                expression_text += line[col_offset:end_col_offset]
            elif line_num == end_lineno:
                expression_text += line[:end_col_offset]
            elif line_num == lineno:
                expression_text += line[col_offset:]            
            else:
                expression_text += line
            line_num += 1
        
        return expression_text

    def print_code(self, file1, file2):
        if self.expression1 != None:
            print(f'{self.mod_type}  from line {self.expression1.lineno} of file A:\n{self.get_text_between_line_col(
                file1, self.expression1.lineno, self.expression1.col_offset, self.expression1.end_lineno, self.expression1.end_col_offset)}')
        elif self.expression2 != None:
            print(f'{self.mod_type} from line {self.expression2.lineno} of file B\n{self.get_text_between_line_col(
                file2, self.expression2.lineno, self.expression2.col_offset, self.expression2.end_lineno, self.expression2.end_col_offset
                )}')


def record_diff2(diffs:list[Diff], stmt1: stmt, stmt2: stmt, modification_type: str):
    diffs.append(Diff(modification_type, stmt1, stmt2))

def generate_ast(filepath: str):
    with open(filepath, 'r') as f:
        d = f.read()
    
    tree = ast.parse(d)

    return tree

def compare_Constant(c1: Constant, c2:Constant):
    if c1.value != c2.value:
        return False
    return True

def compare_value(c1, c2):
    if type(c1) != type(c2):
        return False

    c1_type = type(c1)

    if c1_type == Constant:
        are_equal = c1.value == c2.value
    elif c1_type == Name: # probably doesn't belong here as this is not a value but o well
        are_equal = c1.id == c2.id
    else:
        raise Exception(f'Unknown value type: {type(c1)} on line {c1.lineno}')    

    return are_equal

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

        if not compare_value(cmp1, cmp2):
            are_equal = False
        
        o1 = c1.ops[i1_cursor]
        o2 = c2.ops[i2_cursor]

        if type(o1) != type(o2):
            are_equal = False
            
        i1_cursor += 1
        i2_cursor += 1

    for comparator in c1.comparators[i1_cursor:]:
        are_equal = False
    for comparator in c2.comparators[i2_cursor:]:
        are_equal = False

    return are_equal

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
        elif isinstance(node, Return):
            flattened.extend(flatten_ast_with_structure(node.value))
    
    return flattened

def node_equality(node1, node2):
    if type(node1) != type(node2):
        return False
    
    if isinstance(node1, (BoolOp, If, While, For, Return, BinOp)):
        return True  # We flattened these, so just a type check is good
    elif isinstance(node1, Name):
        return node1.id == node2.id
    elif isinstance(node1, Constant):
        return compare_Constant(node1, node2)
    elif isinstance(node1, Compare):
        return compare_Compare(node1, node2)
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
            lcs_result.append((X[i-1], Y[j-1]))
            i -= 1
            j -= 1
        elif L[i-1][j] > L[i][j-1]:
            i -= 1
        else:
            j -= 1

    return list(reversed(lcs_result))

def compare_stmtlist_lcs(slist1: list[stmt], slist2: list[stmt], diffs: list[Diff]):
    flat1 = flatten_ast_with_structure(slist1)
    flat2 = flatten_ast_with_structure(slist2)
    
    print(f'flat1: {flat1}')
    print(f'flat2: {flat2}')
    lcs_result = lcs_flattened(flat1, flat2)

    print(f'lcs: {lcs_result}')

    for statement in flat1:
        if statement not in [x[0] for x in lcs_result] and not isinstance(statement, BoolOp):
            record_diff2(diffs, statement, None, 'deletion')
            
    for statement in flat2:
        if statement not in [x[1] for x in lcs_result] and not isinstance(statement, BoolOp):
            record_diff2(diffs, None, statement, 'addition')
    
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