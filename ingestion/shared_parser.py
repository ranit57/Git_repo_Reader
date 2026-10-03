from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Language, Parser


@dataclass
class ParsedTree:
    tree: object
    source: str
    language: str
    path: str


LANGUAGE_MODULES = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "java": "tree_sitter_java",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
}


class SharedParser:
    def __init__(self):
        self._parsers: dict[str, Parser] = {}

    def parse(
        self,
        path: Path,
        language: str,
        repo_root: Path | None = None,
    ) -> ParsedTree:
        if language not in LANGUAGE_MODULES:
            raise ValueError(
                f"Unsupported language: {language}"
            )

        source = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        parser = self._get_parser(language)
        tree = parser.parse(
            source.encode("utf-8")
        )

        display_path = path.name
        if repo_root is not None:
            display_path = path.relative_to(repo_root).as_posix()

        return ParsedTree(
            tree=tree,
            source=source,
            language=language,
            path=display_path,
        )

    def _get_parser(self, language: str) -> Parser:
        if language in self._parsers:
            return self._parsers[language]

        module_name = LANGUAGE_MODULES[language]

        module = __import__(module_name)

        # tree-sitter language packages expose language()
        language_factory = getattr(module, "language")
        ts_language = Language(language_factory())

        parser = Parser(ts_language)
        self._parsers[language] = parser

        return parser
