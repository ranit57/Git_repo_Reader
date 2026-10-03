from models.types import QueryResult


class ResultMerger:
    def merge(
        self,
        results: list[QueryResult],
    ) -> list[QueryResult]:
        merged: dict[str, QueryResult] = {}

        for result in results:
            key = (
                result.symbol_id
                or result.file_id
                or f"{result.source}:{len(merged)}"
            )

            if key not in merged:
                merged[key] = result
                continue

            existing = merged[key]

            # pgvector content is authoritative.
            if (
                result.source == "pgvector"
                and result.content
            ):
                existing.content = result.content
                existing.start_line = result.start_line
                existing.end_line = result.end_line

            if result.file_path:
                existing.file_path = result.file_path

            if result.relationships:
                existing.relationships.extend(
                    result.relationships
                )

            if result.score is not None:
                if (
                    existing.score is None
                    or result.score > existing.score
                ):
                    existing.score = result.score

            existing.metadata.update(
                result.metadata
            )

        return list(merged.values())