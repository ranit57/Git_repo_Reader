from dataclasses import dataclass, field
from typing import Any, Literal


EdgeType = Literal[
    "CALLS",
    "IMPORTS",
    "INHERITS",
    "CALLS_EXTERNAL",
]

FileType = Literal[
    "source",
    "test",
    "config",
    "doc",
    "generated",
    "vendored",
]


@dataclass
class FileRecord:
    file_id: str
    repo_id: str
    path: str
    language: str | None
    file_type: FileType
    loc: int
    content_hash: str


@dataclass
class Symbol:
    symbol_id: str
    name: str
    kind: str
    file_id: str
    file_path: str
    start_line: int
    end_line: int
    qualified_name: str | None = None


@dataclass
class Edge:
    source_symbol_id: str
    edge_type: EdgeType
    target: str
    resolved: bool
    target_symbol_id: str | None = None


@dataclass
class Chunk:
    chunk_id: str
    file_id: str
    symbol_id: str
    start_line: int
    end_line: int
    content: str
    embedding: list[float] | None = None


@dataclass
class Dependency:
    name: str
    version: str | None = None


@dataclass
class QueryResult:
    source: Literal["postgres", "pgvector", "neo4j"]
    symbol_id: str | None = None
    file_id: str | None = None
    file_path: str | None = None
    content: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    relationships: list[dict[str, Any]] = field(default_factory=list)
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
