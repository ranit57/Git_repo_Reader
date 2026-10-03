from dataclasses import dataclass
from pathlib import Path

from ingestion.shared_parser import ParsedTree
from models.types import Edge, Symbol


DEFINITION_NODES = {
    # Python
    "function_definition": "function",
    "method_definition": "method",
    "class_definition": "class",
    # JavaScript / TypeScript
    "function_declaration": "function",
    "function_expression": "function",
    "arrow_function": "function",
    "method_definition": "method",
    "method_declaration": "method",
    "class_declaration": "class",
}


@dataclass
class ASTParseResult:
    symbols: list[Symbol]
    edges: list[Edge]


class ASTParser:
    def parse(
        self,
        parsed: ParsedTree,
        repo_id: str,
        file_id: str,
    ) -> ASTParseResult:
        symbols: list[Symbol] = []
        edges: list[Edge] = []

        root = parsed.tree.root_node

        self._extract_symbols(
            root,
            parsed,
            repo_id,
            file_id,
            symbols,
        )

        symbol_names = {
            symbol.name: symbol
            for symbol in symbols
        }

        self._extract_edges(
            root,
            parsed,
            symbol_names,
            symbols,
            edges,
        )

        return ASTParseResult(
            symbols=symbols,
            edges=edges,
        )

    def _extract_symbols(
        self,
        node,
        parsed: ParsedTree,
        repo_id: str,
        file_id: str,
        symbols: list[Symbol],
        parent_name: str | None = None,
    ) -> None:
        node_type = node.type

        if node_type in DEFINITION_NODES:
            kind = DEFINITION_NODES[node_type]
            name = self._definition_name(
                node,
                parsed.source,
            )

            if name:
                qualified_name = (
                    f"{parent_name}.{name}"
                    if parent_name
                    else name
                )

                relative_path = Path(parsed.path).as_posix()

                symbol_id = (
                    f"{repo_id}:{relative_path}:"
                    f"{qualified_name}"
                )

                symbols.append(
                    Symbol(
                        symbol_id=symbol_id,
                        name=name,
                        kind=kind,
                        file_id=file_id,
                        file_path=relative_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        qualified_name=qualified_name,
                    )
                )

                parent_name = qualified_name

        for child in node.children:
            self._extract_symbols(
                child,
                parsed,
                repo_id,
                file_id,
                symbols,
                parent_name,
            )

    def _extract_edges(
        self,
        root,
        parsed: ParsedTree,
        symbol_names: dict[str, Symbol],
        symbols: list[Symbol],
        edges: list[Edge],
    ) -> None:
        current_symbol = None

        self._walk_edges(
            root,
            parsed,
            symbol_names,
            symbols,
            edges,
            current_symbol,
        )

    def _walk_edges(
        self,
        node,
        parsed,
        symbol_names,
        symbols,
        edges,
        current_symbol,
    ):
        if node.type in DEFINITION_NODES:
            name = self._definition_name(
                node,
                parsed.source,
            )

            if name:
                current_symbol = symbol_names.get(name)

        if current_symbol:
            self._extract_call(
                node,
                parsed,
                current_symbol,
                symbol_names,
                edges,
            )

        self._extract_import(
            node,
            parsed,
            current_symbol,
            symbol_names,
            edges,
        )

        for child in node.children:
            self._walk_edges(
                child,
                parsed,
                symbol_names,
                symbols,
                edges,
                current_symbol,
            )

    def _extract_call(
        self,
        node,
        parsed,
        source_symbol,
        symbol_names,
        edges,
    ):
        if node.type not in {
            "call",
            "call_expression",
            "method_invocation",
        }:
            return

        function_node = node.child_by_field_name(
            "function"
        )

        if function_node is None:
            function_node = node.child_by_field_name(
                "name"
            )

        if function_node is None:
            return

        target = self._node_text(
            function_node,
            parsed.source,
        )

        target_name = target.split(".")[-1]
        target_symbol = symbol_names.get(target_name)

        edges.append(
            Edge(
                source_symbol_id=source_symbol.symbol_id,
                edge_type="CALLS",
                target=target,
                resolved=target_symbol is not None,
                target_symbol_id=(
                    target_symbol.symbol_id
                    if target_symbol
                    else None
                ),
            )
        )

    def _extract_import(
        self,
        node,
        parsed,
        current_symbol,
        symbol_names,
        edges,
    ):
        if node.type not in {
            "import_statement",
            "import_from_statement",
            "import_declaration",
        }:
            return

        target = self._node_text(
            node,
            parsed.source,
        )

        if not target:
            return

        source_id = (
            current_symbol.symbol_id
            if current_symbol
            else f"file:{parsed.path}"
        )

        target_name = target.strip()

        edges.append(
            Edge(
                source_symbol_id=source_id,
                edge_type="IMPORTS",
                target=target_name,
                resolved=target_name in symbol_names,
                target_symbol_id=(
                    symbol_names[target_name].symbol_id
                    if target_name in symbol_names
                    else None
                ),
            )
        )

    @staticmethod
    def _definition_name(node, source):
        name_node = node.child_by_field_name("name")

        if name_node is None:
            # For JavaScript function_expression/arrow_function assigned to variable,
            # the name is in the parent variable_declarator's identifier
            if node.type in {"function_expression", "arrow_function"}:
                parent = node.parent
                if parent and parent.type == "variable_declarator":
                    for child in parent.children:
                        if child.type == "identifier":
                            return source[
                                child.start_byte:child.end_byte
                            ]
            
            for child in node.children:
                if child.type in {
                    "identifier",
                    "type_identifier",
                }:
                    return source[
                        child.start_byte:child.end_byte
                    ]

            return None

        return source[
            name_node.start_byte:name_node.end_byte
        ]

    @staticmethod
    def _node_text(node, source):
        return source[
            node.start_byte:node.end_byte
        ].strip()