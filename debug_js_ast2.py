from tree_sitter import Language, Parser
import tree_sitter_javascript

ts_language = Language(tree_sitter_javascript.language())
parser = Parser(ts_language)

# Read the actual app.js
with open(r'\tmp\repo-ai-engineer\repos\PCB_Fault_Detection\PCB_Fault_Detection\app.js', 'r') as f:
    code = f.read()

tree = parser.parse(code.encode('utf-8'))

def print_tree(node, indent=0):
    prefix = '  ' * indent
    if node.start_byte != node.end_byte:
        text = code[node.start_byte:node.end_byte].replace('\n', '\\n')[:80]
        print(f'{prefix}{node.type}: "{text}"')
    else:
        print(f'{prefix}{node.type}')
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(tree.root_node)