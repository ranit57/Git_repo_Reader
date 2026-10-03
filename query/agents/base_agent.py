from abc import ABC, abstractmethod
from models.types import QueryResult
from storage.neo4j_client import Neo4jClient
from storage.postgres_client import PostgresClient


class BaseAgent(ABC):
    def __init__(
        self,
        postgres: PostgresClient,
        neo4j: Neo4jClient,
        embedder,
    ):
        self.postgres = postgres
        self.neo4j = neo4j
        self.embedder = embedder

    @abstractmethod
    def retrieve(
        self,
        query: str,
        repo_id: str,
    ) -> list[QueryResult]:
        """Retrieve candidates relevant to the query."""
        raise NotImplementedError

    def semantic_search(
        self,
        query: str,
        repo_id: str,
        limit: int = 5,
    ) -> list[QueryResult]:
        embedding = self.embedder.embed(query)

        rows = self.postgres.search_chunks(
            repo_id,
            embedding,
            limit,
        )

        return [
            QueryResult(
                source="pgvector",
                symbol_id=row["symbol_id"],
                file_id=str(row["file_id"]),
                file_path=row.get("file_path"),
                content=row["content"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                score=float(row["score"]),
            )
            for row in rows
        ]

    def file_search(
        self,
        repo_id: str,
        limit: int = 25,
    ) -> list[QueryResult]:
        rows = self.postgres.list_files(repo_id)[:limit]

        return [
            QueryResult(
                source="postgres",
                file_id=str(row["file_id"]),
                file_path=row["path"],
                metadata={
                    "language": row["language"],
                    "file_type": row["file_type"],
                    "loc": row["loc"],
                },
            )
            for row in rows
        ]

    def file_path_search(
        self,
        repo_id: str,
        path: str,
    ) -> QueryResult | None:
        normalized_path = path.strip().strip("\"'`").replace("\\", "/")
        if normalized_path.startswith("./"):
            normalized_path = normalized_path[2:]

        if (
            not normalized_path
            or normalized_path.startswith(".git/")
            or "/.git/" in normalized_path
        ):
            return None

        row = self.postgres.get_file(repo_id, normalized_path)

        if not row or row["file_type"] == "generated":
            return None

        return QueryResult(
            source="postgres",
            file_id=str(row["file_id"]),
            file_path=row["path"],
            start_line=1,
            end_line=row["loc"],
            metadata={
                "language": row["language"],
                "file_type": row["file_type"],
                "loc": row["loc"],
            },
        )

    def relationship_search(
        self,
        symbol_id: str,
    ) -> list[QueryResult]:
        relationships = self.neo4j.find_relationships(
            symbol_id
        )

        return [
            QueryResult(
                source="neo4j",
                symbol_id=symbol_id,
                relationships=relationships,
            )
        ]

    def enrich_relationships(
        self,
        results: list[QueryResult],
    ) -> list[QueryResult]:
        enriched = []

        for result in results:
            if result.symbol_id:
                result.relationships = (
                    self.neo4j.find_relationships(
                        result.symbol_id
                    )
                )

            enriched.append(result)

        return enriched
