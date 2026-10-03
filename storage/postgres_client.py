from typing import Any, Iterable
import uuid

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class PostgresClient:
    def __init__(self, database_url: str):
        self.pool = ConnectionPool(
            conninfo=database_url,
            kwargs={"row_factory": dict_row},
            open=False,
        )
        self.pool.open()

    def close(self) -> None:
        self.pool.close()

    def _ensure_uuid(self, value: str) -> str:
        """Ensure the value is a valid UUID, generate one if not."""
        try:
            uuid.UUID(value)
            return value
        except (ValueError, AttributeError):
            return str(uuid.uuid4())

    def upsert_file(self, file: Any) -> str:
        query = """
        INSERT INTO files (
            file_id, repo_id, path, language,
            file_type, loc, content_hash
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (repo_id, path)
        DO UPDATE SET
            language = EXCLUDED.language,
            file_type = EXCLUDED.file_type,
            loc = EXCLUDED.loc,
            content_hash = EXCLUDED.content_hash
        """

        file_id = self._ensure_uuid(file.file_id)

        with self.pool.connection() as conn:
            # Use RETURNING to get the actual file_id in case of an update
            res = conn.execute(
                query + "\nRETURNING file_id",
                (
                    file_id,
                    file.repo_id,
                    file.path,
                    file.language,
                    file.file_type,
                    file.loc,
                    file.content_hash,
                ),
            ).fetchone()

            persisted_id = res["file_id"] if res else file_id
            # psycopg returns UUID objects for UUID columns; convert to string
            return str(persisted_id)

    def upsert_chunk(self, chunk: Any) -> None:
        query = """
        INSERT INTO chunks (
            chunk_id,
            file_id,
            symbol_id,
            start_line,
            end_line,
            content,
            embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol_id)
        DO UPDATE SET
            file_id = EXCLUDED.file_id,
            start_line = EXCLUDED.start_line,
            end_line = EXCLUDED.end_line,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding
        """

        with self.pool.connection() as conn:
            conn.execute(
                query,
                (
                    chunk.chunk_id,
                    chunk.file_id,
                    chunk.symbol_id,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.content,
                    chunk.embedding,
                ),
            )

    def upsert_chunks(self, chunks: Iterable[Any]) -> None:
        with self.pool.connection() as conn:
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO chunks (
                        chunk_id, file_id, symbol_id,
                        start_line, end_line, content, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol_id)
                    DO UPDATE SET
                        file_id = EXCLUDED.file_id,
                        start_line = EXCLUDED.start_line,
                        end_line = EXCLUDED.end_line,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        chunk.chunk_id,
                        chunk.file_id,
                        chunk.symbol_id,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.content,
                        chunk.embedding,
                    ),
                )

    def get_file(self, repo_id: str, path: str) -> dict | None:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM files
                WHERE repo_id = %s AND path = %s
                """,
                (repo_id, path),
            ).fetchone()

    def get_chunk(self, symbol_id: str) -> dict | None:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM chunks
                WHERE symbol_id = %s
                """,
                (symbol_id,),
            ).fetchone()

    def search_chunks(
        self,
        repo_id: str,
        embedding: list[float],
        limit: int = 10,
    ) -> list[dict]:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT
                    chunks.chunk_id,
                    chunks.file_id,
                    chunks.symbol_id,
                    chunks.start_line,
                    chunks.end_line,
                    chunks.content,
                    files.path AS file_path,
                    1 - (chunks.embedding <=> %s::vector) AS score
                FROM chunks
                JOIN files ON files.file_id = chunks.file_id
                WHERE files.repo_id = %s
                ORDER BY score DESC
                LIMIT %s
                """,
                (embedding, repo_id, limit),
            ).fetchall()

    def list_files(self, repo_id: str) -> list[dict]:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM files
                WHERE repo_id = %s
                ORDER BY path
                """,
                (repo_id,),
            ).fetchall()

    def count_files(self, repo_id: str) -> int:
        with self.pool.connection() as conn:
            return conn.execute(
                "SELECT count(*) FROM files WHERE repo_id = %s",
                (repo_id,),
            ).fetchone()["count"]

    def count_chunks(self, repo_id: str) -> int:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT count(*)
                FROM chunks
                JOIN files ON files.file_id = chunks.file_id
                WHERE files.repo_id = %s
                """,
                (repo_id,),
            ).fetchone()["count"]

    def sample_chunks(self, repo_id: str, limit: int = 5) -> list[dict]:
        with self.pool.connection() as conn:
            return conn.execute(
                """
                SELECT c.chunk_id, c.symbol_id, c.start_line, c.end_line, c.content, f.path
                FROM chunks c
                JOIN files f ON f.file_id = c.file_id
                WHERE f.repo_id = %s
                LIMIT %s
                """,
                (repo_id, limit),
            ).fetchall()

    def ping(self) -> None:
        """Quick connectivity check for Postgres."""
        with self.pool.connection() as conn:
            conn.execute("SELECT 1")
