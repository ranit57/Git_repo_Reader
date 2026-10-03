from pathlib import Path

from models.types import QueryResult


class SourceLookup:
    def __init__(self, clone_base_dir: Path):
        self.clone_base_dir = Path(clone_base_dir)

    def resolve(
        self,
        results: list[QueryResult],
        repo_id: str,
    ) -> list[QueryResult]:
        resolved = []

        for result in results:
            if result.source == "postgres":
                self._load_source(result, repo_id)

            # pgvector already contains code content.
            # Neo4j contains relationships, not code.
            resolved.append(result)

        return resolved

    def _load_source(self, result: QueryResult, repo_id: str) -> None:
        if not result.file_path:
            return
        if result.start_line is None and result.end_line is None:
            return

        path = self.clone_base_dir / repo_id / result.file_path

        if not path.exists():
            return

        lines = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()

        start = (
            result.start_line or 1
        )
        end = (
            result.end_line or len(lines)
        )

        result.content = "\n".join(
            lines[start - 1:end]
        )
