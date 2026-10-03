from pathlib import Path

from ingestion.ast_parser import ASTParser
from ingestion.code_chunker import CodeChunker
import uuid
from models.types import Chunk
from ingestion.config_analyzer import ConfigAnalyzer
from ingestion.dependency_builder import DependencyBuilder
from ingestion.embedding import EmbeddingModel
from ingestion.file_analyzer import FileAnalyzer
from ingestion.shared_parser import SharedParser
from storage.neo4j_client import Neo4jClient
from storage.postgres_client import PostgresClient


class IngestionOrchestrator:
    def __init__(
        self,
        postgres: PostgresClient,
        neo4j: Neo4jClient,
        embedder: EmbeddingModel,
    ):
        self.postgres = postgres
        self.neo4j = neo4j
        self.embedder = embedder

        self.file_analyzer = FileAnalyzer()
        self.shared_parser = SharedParser()
        self.ast_parser = ASTParser()
        self.config_analyzer = ConfigAnalyzer()
        self.dependency_builder = DependencyBuilder()
        self.chunker = CodeChunker()

    def preflight(self) -> None:
        """Perform quick checks for external dependencies used during ingestion.

        Raises a RuntimeError with a helpful message if a check fails.
        """
        # Check Postgres connectivity
        try:
            self.postgres.ping()
        except Exception as exc:
            raise RuntimeError(
                f"Postgres connectivity check failed: {exc}"
            ) from exc

        # Check Neo4j connectivity
        try:
            self.neo4j.verify_connection()
        except Exception as exc:
            raise RuntimeError(
                f"Neo4j connectivity check failed: {exc}"
            ) from exc

        # Check embedding service
        try:
            # A lightweight probe — do NOT rely on the returned vector.
            self.embedder.embed("__repo_ai_probe__")
        except Exception as exc:
            raise RuntimeError(
                f"Embedding service check failed: {exc}"
            ) from exc

    def run(
        self,
        repo_path: Path,
        repo_id: str,
        progress_callback=None,
    ) -> None:
        # Preflight checks: DB, Neo4j, and embedding service
        self.preflight()

        def update_progress(step: str, message: str, agent: str | None = None) -> None:
            if progress_callback:
                progress_callback(step, message, agent)

        update_progress("analyzing", "Analyzing repository", "file_analyzer")

        # 1. Analyze all files first.
        files = self.file_analyzer.analyze(repo_path)

        # Validate that required tree-sitter language modules are available for files
        languages = {f.language for f in files if f.language}
        missing = []
        from ingestion.shared_parser import LANGUAGE_MODULES

        for lang in languages:
            module = LANGUAGE_MODULES.get(lang)
            if not module:
                continue
            try:
                __import__(module)
            except Exception:
                missing.append(module)

        if missing:
            raise RuntimeError(
                f"Missing tree-sitter language packages: {', '.join(missing)}. "
                "Install the packages or remove unsupported files."
            )

        # 2. Commit file metadata before chunks.
        for file_record in files:
            # upsert_file returns the actual file_id stored (may differ from
            # analyzer-generated id if an existing row is present). Use that
            # id for subsequent chunk inserts to satisfy foreign key.
            persisted_id = self.postgres.upsert_file(file_record)
            file_record.file_id = persisted_id

        unresolved_edges = []
        dependencies = []

        # 3-4. Parse source files and analyze configs.
        for file_record in files:
            path = repo_path / file_record.path
            update_progress("analyzing", f"Analyzing file {file_record.path}", "file_analyzer")

            if file_record.file_type == "config":
                update_progress("analyzing", f"Analyzing config {file_record.path}", "config_analyzer")
                dependencies.extend(
                    self.config_analyzer.analyze(path)
                )
                self._chunk_text_file(
                    path,
                    file_record.file_id,
                    repo_id,
                    file_record.path,
                    progress_callback=progress_callback,
                    agent="config_chunker",
                )
                continue

            if file_record.file_type not in {"source", "test"}:
                # Fallback: handle plain-text/document files (markdown, txt)
                if file_record.file_type == "doc":
                    try:
                        self._chunk_text_file(
                            path,
                            file_record.file_id,
                            repo_id,
                            file_record.path,
                            progress_callback=progress_callback,
                            agent="doc_chunker",
                        )
                    except Exception as exc:
                        update_progress("skipping", f"Skipping {file_record.path}: {exc}", "file_analyzer")
                        print(f"Skipping {file_record.path}: {exc}")

                continue

            if not file_record.language:
                continue

            try:
                update_progress("parsing", f"Parsing {file_record.path}", "shared_parser")
                parsed = self.shared_parser.parse(
                    path,
                    file_record.language,
                    repo_path,
                )

                update_progress("parsing", f"AST parsing {file_record.path}", "ast_parser")
                ast_result = self.ast_parser.parse(
                    parsed,
                    repo_id,
                    file_record.file_id,
                )

                # Resolved edges go directly to Neo4j.
                for symbol in ast_result.symbols:
                    self.neo4j.upsert_symbol(symbol)

                for edge in ast_result.edges:
                    if edge.resolved:
                        self.neo4j.upsert_relationship(
                            source_symbol_id=edge.source_symbol_id,
                            target_symbol_id=edge.target_symbol_id,
                            relationship_type=edge.edge_type,
                        )
                    else:
                        unresolved_edges.append(edge)

                update_progress("chunking", f"Chunking {file_record.path}", "code_chunker")
                chunks = self.chunker.chunk(
                    parsed,
                    file_record.file_id,
                    repo_id,
                )

                if not chunks:
                    chunks = self._build_text_chunks(
                        path,
                        file_record.file_id,
                        repo_id,
                        file_record.path,
                        "file",
                    )

                update_progress("embedding", f"Embedding chunks for {file_record.path}", "embedding_model")
                embeddings = self.embedder.embed_many(
                    [chunk.content for chunk in chunks]
                )

                for chunk, embedding in zip(
                    chunks,
                    embeddings,
                ):
                    chunk.embedding = embedding

                self.postgres.upsert_chunks(chunks)

            except Exception as exc:
                update_progress("skipping", f"Skipping {file_record.path}: {exc}", "file_analyzer")
                print(
                    f"Skipping {file_record.path}: {exc}"
                )

        # 5-6. Resolve unresolved external dependencies.
        external_edges = self.dependency_builder.resolve(
            unresolved_edges,
            dependencies,
        )

        for edge in external_edges:
            if not edge.resolved:
                continue

            self.neo4j.upsert_package(
                edge.package_name,
                edge.package_version,
            )

            package_id = (
                f"package:{edge.package_name}"
            )

            self.neo4j.upsert_relationship(
                source_symbol_id=edge.from_symbol_id,
                target_symbol_id=package_id,
                relationship_type=edge.edge_type,
            )

    def _chunk_text_file(
        self,
        path: Path,
        file_id: str,
        repo_id: str,
        file_path: str,
        progress_callback=None,
        agent: str = "file_chunker",
    ) -> None:
        if progress_callback:
            progress_callback("chunking", f"Chunking {file_path}", agent)

        chunks = self._build_text_chunks(
            path,
            file_id,
            repo_id,
            file_path,
            agent.replace("_chunker", ""),
        )

        if not chunks:
            return

        if progress_callback:
            progress_callback("embedding", f"Embedding chunks for {file_path}", "embedding_model")

        embeddings = self.embedder.embed_many([chunk.content for chunk in chunks])

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        self.postgres.upsert_chunks(chunks)

    @staticmethod
    def _build_text_chunks(
        path: Path,
        file_id: str,
        repo_id: str,
        file_path: str,
        chunk_kind: str,
    ) -> list[Chunk]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        if not lines:
            return []

        max_lines = 80
        chunks = []

        for index in range(0, len(lines), max_lines):
            part_lines = lines[index:index + max_lines]
            start_line = index + 1
            end_line = index + len(part_lines)
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    file_id=file_id,
                    symbol_id=f"{repo_id}:{file_path}:{chunk_kind}:{start_line}",
                    start_line=start_line,
                    end_line=end_line,
                    content="\n".join(part_lines),
                )
            )

        return chunks
