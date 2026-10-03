import uuid

from ingestion.shared_parser import ParsedTree
from models.types import Chunk


class CodeChunker:
    def chunk(
        self,
        parsed: ParsedTree,
        file_id: str,
        repo_id: str,
    ) -> list[Chunk]:
        chunks = []

        for node in self._definition_nodes(
            parsed.tree.root_node
        ):
            name = self._get_definition_name(node, parsed.source)

            if name is None:
                continue

            symbol_id = self._symbol_id(
                repo_id,
                parsed.path,
                name,
            )

            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            content = "\n".join(
                parsed.source.splitlines()[
                    start_line - 1:end_line
                ]
            )

            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    file_id=file_id,
                    symbol_id=symbol_id,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                )
            )

        return chunks

    def _get_definition_name(self, node, source: str) -> str | None:
        """Extract name from definition node, handling JS function expressions."""
        name_node = node.child_by_field_name("name")

        if name_node is not None:
            return self._node_text(name_node, source)

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

        return None

    def _definition_nodes(self, node):
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

        if node.type in definition_types:
            yield node

        for child in node.children:
            yield from self._definition_nodes(child)

    @staticmethod
    def _node_text(node, source: str) -> str:
        return source[
            node.start_byte:node.end_byte
        ].strip()

    @staticmethod
    def _symbol_id(
        repo_id: str,
        path: str,
        name: str,
    ) -> str:
        return f"{repo_id}:{path}:{name}"