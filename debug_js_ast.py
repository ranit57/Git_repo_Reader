from tree_sitter import Language, Parser
import tree_sitter_javascript

ts_language = Language(tree_sitter_javascript.language())
parser = Parser(ts_language)

code = '''
var infer = function() {
    console.log('hello');
};

function foo() {
    bar();
}

const baz = () => {
    qux();
};
'''

tree = parser.parse(code.encode('utf-8'))

def print_tree(node, indent=0):
    prefix = '  ' * indent
    if node.start_byte != node.end_byte:
        text = code[node.start_byte:node.end_byte].replace('\n', '\\n')[:50]
        print(f'{prefix}{node.type}: "{text}"')
    else:
        print(f'{prefix}{node.type}')
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(tree.root_node)