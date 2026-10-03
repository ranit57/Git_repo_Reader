from config.settings import settings
from ingestion.cloner import RepositoryCloner
from ingestion.shared_parser import SharedParser

cloner = RepositoryCloner(settings.clone_base_dir)
repo_id = cloner.repo_id_from_url('https://github.com/Kiranpatil5/PCB_Fault_Detection')
repo_path = cloner.clone('https://github.com/Kiranpatil5/PCB_Fault_Detection', repo_id)

js_path = repo_path / 'PCB_Fault_Detection' / 'app.js'

shared_parser = SharedParser()
parsed = shared_parser.parse(js_path, 'javascript', repo_path)

# Check what nodes are found
def find_def_nodes(node, definition_types, depth=0):
    if node.type in definition_types:
        name_node = node.child_by_field_name("name")
        name = None
        if name_node:
            name = parsed.source[name_node.start_byte:name_node.end_byte]
        else:
            # Check parent for variable_declarator
            parent = node.parent
            if parent and parent.type == "variable_declarator":
                for child in parent.children:
                    if child.type == "identifier":
                        name = parsed.source[child.start_byte:child.end_byte]
                        break
        print(f"{'  '*depth}{node.type}: name={name}")
    
    for child in node.children:
        find_def_nodes(child, definition_types, depth+1)

definition_types = {
    "function_definition",
    "method_definition",
    "class_definition",
    "function_declaration",
    "function_expression",
    "arrow_function",
    "method_declaration",
    "class_declaration",
}

find_def_nodes(parsed.tree.root_node, definition_types)