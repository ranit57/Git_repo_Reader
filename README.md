# Repo AI Engineer

An AI-powered software engineering system that analyzes GitHub repositories and allows users to ask natural-language questions about their codebase.

The system ingests a repository, extracts file metadata, code structure, symbols, relationships, dependencies, and semantic code chunks, then stores the information across PostgreSQL/pgvector and Neo4j. At query time, specialized agents retrieve and combine this information to generate grounded answers.

---

## 1. Architecture

The system consists of two major pipelines:

* **Repository Ingestion Pipeline**
* **Query Pipeline**

### Overall Flow

```text
                         ┌─────────────────────┐
                         │     GitHub Repo     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Repository Clone  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    File Analyzer    │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
            Source Files       Config Files       Generated/
                 │                  │              Vendored
                 ▼                  ▼                  │
         ┌──────────────┐   ┌───────────────┐          │
         │Shared Parser │   │Config Analyzer│          │
         └──────┬───────┘   └───────┬───────┘          │
                │                   │                  │
          ┌─────┴─────┐             ▼                  │
          ▼           ▼      ┌─────────────────┐       │
    AST Parser   Code Chunker │Dependency       │       │
          │           │       │Builder          │       │
          │           ▼       └────────┬────────┘       │
          │      Embeddings           │                │
          │           │               │                │
          ▼           ▼               ▼                │
       Neo4j      PostgreSQL        Neo4j              │
     Relationships  + pgvector   External Deps        │
          │           │               │                │
          └───────────┴───────┬───────┴────────────────┘
                              │
                              ▼
                         Query Pipeline
                              │
                              ▼
                       Agent Orchestrator
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       Code Navigator   Retrieval QA    Bug Detector
                              │
                              ▼
                      Document Analyzer
                              │
                              ▼
                   PostgreSQL / pgvector
                              +
                           Neo4j
                              │
                              ▼
                       Source Lookup
                              │
                              ▼
                         Result Merge
                              │
                              ▼
                       LLM Synthesizer
                              │
                              ▼
                         Final Answer
```

---

# 2. Repository Ingestion Pipeline

The ingestion pipeline converts a raw GitHub repository into structured, queryable data.

```text
GitHub URL
    │
    ▼
Local Clone
    │
    ▼
File Analyzer
    │
    ├── source ──► Shared Parser
    │                  ├──► AST Parser ──► Neo4j
    │                  └──► Code Chunker
    │                           │
    │                           ▼
    │                       Embeddings
    │                           │
    │                           ▼
    │                       PostgreSQL
    │
    └── config ──► Config Analyzer
                       │
                       ▼
                 Dependency Builder
                       │
                       ▼
                     Neo4j
```

The ingestion pipeline follows a strict ordering:

1. Clone repository.
2. Analyze all files.
3. Commit file metadata to PostgreSQL.
4. Parse supported source files.
5. Extract symbols and relationships.
6. Analyze configuration/manifests.
7. Resolve external dependencies.
8. Generate code chunks.
9. Generate embeddings.
10. Store chunks in PostgreSQL.
11. Store relationships in Neo4j.

A source file is parsed only once. The resulting syntax tree is shared between the AST Parser and Code Chunker.

---

# 3. File Analyzer

The File Analyzer runs before any parsing.

For every repository file it determines:

* Language
* File type
* Lines of code
* Content hash

Supported file classifications:

```text
source
test
config
generated
vendored
```

Example:

```text
app/services/payment.py
    language: python
    file_type: source
    loc: 63
```

Generated and vendored files are excluded from further processing.

---

# 4. Shared Parser

The Shared Parser uses Tree-sitter to build one syntax tree for each supported source file.

```text
Source File
    │
    ▼
Shared Parser
    │
    ▼
Syntax Tree
    │
    ├──────────────► AST Parser
    │
    └──────────────► Code Chunker
```

The syntax tree contains node locations including:

* Start line
* End line
* Node type
* Source positions

The tree itself is an intermediate in-memory representation and is not persisted.

---

# 5. AST Parser

The AST Parser extracts:

### Symbols

Examples:

```text
Function
Method
Class
```

### Relationships

```text
CALLS
IMPORTS
INHERITS
```

Each relationship is classified as either:

```text
resolved
unresolved
```

Resolved relationships point to symbols defined inside the repository.

Unresolved relationships are passed to the Dependency Builder.

---

# 6. Dependency Builder

The Dependency Builder resolves external references using dependency manifests.

Example:

```text
AST Parser:

process_payment
    │
    └── CALLS → stripe.charge
                     │
                     ▼
              unresolved
```

Manifest:

```text
stripe == 5.4.0
```

Dependency Builder produces:

```text
process_payment
    │
    └── CALLS_EXTERNAL → Package(stripe, 5.4.0)
```

If a dependency cannot be matched, the relationship remains unresolved rather than being silently discarded.

---

# 7. Code Chunking

The Code Chunker consumes the same syntax tree produced by the Shared Parser.

Function and class definitions become chunks.

Example:

```text
symbol_id:
orders-service:payment.py:process_payment

file_id:
f_7c21

start_line:
2

end_line:
7
```

The chunk contains the actual source code:

```python
def process_payment(order_id, amount):
    ...
```

Each chunk is then passed to the embedding model.

---

# 8. Embeddings

The Embedding Model converts each code chunk into a fixed-length vector.

```text
Code Chunk
    │
    ▼
Embedding Model
    │
    ▼
Vector
    │
    ▼
PostgreSQL / pgvector
```

The embedding model is used only for semantic encoding during ingestion. It does not perform generative reasoning.

---

# 9. Storage

## PostgreSQL + pgvector

PostgreSQL stores:

### `files`

```text
file_id
repo_id
path
language
file_type
loc
content_hash
```

### `chunks`

```text
chunk_id
file_id
symbol_id
start_line
end_line
content
embedding
```

The `chunks` table uses pgvector for semantic similarity search.

---

## Neo4j

Neo4j stores the structural relationship graph.

### Node types

```text
Function
Class
File
Package
```

### Relationship types

```text
CALLS
IMPORTS
INHERITS
CALLS_EXTERNAL
```

Example:

```text
(process_payment:Function)
        │
        ├── CALLS ─────────────► (save:Function)
        │
        └── CALLS_EXTERNAL ────► (stripe:Package)
```

---

# 10. `symbol_id` — Cross-Store Join Key

The most important identifier in the architecture is `symbol_id`.

The same symbol uses the same ID in:

```text
PostgreSQL chunks
        │
        │ symbol_id
        ▼
Neo4j graph
```

Example:

```text
orders-service:payment.py:process_payment
```

This allows query-time retrieval to move directly from semantic search results to graph relationships without fuzzy matching.

---

# 11. Query Pipeline

Once a repository has been ingested, users can ask natural-language questions.

```text
User Query
    │
    ▼
Agent Orchestrator
    │
    ▼
Specialized Agent
    │
    ├──► PostgreSQL
    │
    ├──► pgvector
    │
    └──► Neo4j
    │
    ▼
Source Lookup
    │
    ▼
Result Merge
    │
    ▼
LLM Synthesizer
    │
    ▼
Final Answer
```

---

# 12. Specialized Agents

The system contains four query agents.

| Agent             | Primary Focus         | Purpose                                |
| ----------------- | --------------------- | -------------------------------------- |
| Code Navigator    | Neo4j + pgvector      | Understand structure and relationships |
| Retrieval QA      | pgvector              | Answer questions grounded in code      |
| Bug Detector      | Neo4j + pgvector      | Trace potential defects                |
| Document Analyzer | PostgreSQL + pgvector | Summarize files/components             |

Agents share the same underlying storage access pattern but prioritize different retrieval sources.

---

# 13. Source Lookup

Source lookup is intentionally asymmetric.

### PostgreSQL file metadata

Usually requires source lookup because the `files` table does not contain code.

```text
PostgreSQL file metadata
        │
        ▼
Local repository
        │
        ▼
Source code
```

### pgvector

Usually does not require source lookup because the chunk already contains its code.

```text
pgvector chunk
    │
    └── code already available
```

### Neo4j

Does not require source lookup because it provides structural relationships rather than source code.

---

# 14. Result Merge

Results from different stores are normalized into a common representation.

Example:

```text
{
    symbol_id,
    file_path,
    code_snippet,
    relationships,
    metadata
}
```

If the same symbol appears in multiple stores, results are deduplicated using `symbol_id`.

---

# 15. LLM Synthesis

The LLM is used at the final stage.

```text
User Query
    +
Merged Repository Context
    │
    ▼
LLM
    │
    ▼
Grounded Answer
```

The synthesizer should:

* Use retrieved repository evidence.
* Mention relevant file paths.
* Mention line ranges when available.
* Avoid inventing repository facts.
* Clearly indicate when retrieved context is insufficient.

---

# 16. API

The backend uses FastAPI.

## Start the API

```bash
uvicorn api.main:app --reload
```

## Ingest Repository

```http
POST /ingest
```

Request:

```json
{
  "repo_url": "https://github.com/example/orders-service.git"
}
```

Response:

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

## Check Ingestion Status

```http
GET /ingest/{job_id}
```

Possible states include:

```text
queued
cloning
analyzing
parsing
embedding
storing
ready
failed
```

## Query Repository

```http
POST /query
```

Request:

```json
{
  "query": "Where is process_payment defined?"
}
```

Response:

```json
{
  "answer": "..."
}
```

---

# 17. CLI

## Ingest

```bash
python scripts/ingest_repo.py \
    https://github.com/example/orders-service.git
```

## Query

```bash
python scripts/query_repo.py \
    orders-service \
    "Where is process_payment defined?"
```

---

# 18. Frontend

The frontend uses React and Vite.

```text
frontend/
├── package.json
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api/
    │   └── client.js
    └── components/
        ├── IngestPanel.jsx
        ├── ChatPanel.jsx
        ├── AnswerCard.jsx
        └── SourceSnippet.jsx
```

The UI contains:

* Repository ingestion panel
* Ingestion status polling
* Query/chat interface
* Answer display
* Source snippets with file paths and line ranges

---

# 19. Project Structure

```text
repo-ai-engineer/
│
├── README.md
├── pyproject.toml
├── .env.example
│
├── config/
│   └── settings.py
│
├── storage/
│   ├── schema.sql
│   ├── postgres_client.py
│   └── neo4j_client.py
│
├── ingestion/
│   ├── cloner.py
│   ├── orchestrator.py
│   ├── file_analyzer.py
│   ├── shared_parser.py
│   ├── ast_parser.py
│   ├── config_analyzer.py
│   ├── dependency_builder.py
│   ├── code_chunker.py
│   └── embedding.py
│
├── query/
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── code_navigator.py
│   │   ├── retrieval_qa.py
│   │   ├── bug_detector.py
│   │   └── document_analyzer.py
│   ├── source_lookup.py
│   ├── merge.py
│   └── synthesizer.py
│
├── models/
│   ├── types.py
│   └── job_status.py
│
├── api/
│   ├── main.py
│   ├── ingest_routes.py
│   ├── query_routes.py
│   └── job_runner.py
│
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       └── components/
│           ├── IngestPanel.jsx
│           ├── ChatPanel.jsx
│           ├── AnswerCard.jsx
│           └── SourceSnippet.jsx
│
├── scripts/
│   ├── ingest_repo.py
│   └── query_repo.py
│
├── tests/
│   ├── test_file_analyzer.py
│   ├── test_ast_parser.py
│   ├── test_code_chunker.py
│   ├── test_dependency_builder.py
│   └── test_query_orchestrator.py
│
└── docs/
    ├── spec.md
    └── query-pipeline-spec.md
```

---

# 20. Installation

## Requirements

* Python 3.10+
* PostgreSQL
* pgvector extension
* Neo4j
* Git
* Node.js/npm for the frontend
* API key for the configured embedding/LLM provider

## Python Environment

```bash
python -m venv .venv
```

### Linux/macOS

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install the project:

```bash
pip install -e .
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

---

# 21. Environment Configuration

Create a `.env` file from `.env.example`.

Example:

```env
POSTGRES_URL=postgresql://postgres:password@localhost:5432/repo_ai

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_api_key

CLONE_BASE_DIR=/tmp/repo-ai-engineer/repos

PGVECTOR_TOP_K=10
```

---

# 22. Database Initialization

Initialize PostgreSQL using:

```bash
psql "$POSTGRES_URL" -f storage/schema.sql
```

The schema creates the required `files` and `chunks` tables and enables pgvector.

---

# 23. Running Tests

Run the complete test suite:

```bash
pytest
```

Run an individual test:

```bash
pytest tests/test_ast_parser.py
```

---

# 24. Design Principles

The implementation follows these core architectural rules:

1. File analysis happens before parsing.
2. A source file is parsed only once.
3. AST Parser and Code Chunker consume the same syntax tree.
4. Resolved internal relationships go directly to Neo4j.
5. Unresolved external relationships go through Dependency Builder.
6. `symbol_id` is the cross-store join key.
7. `chunks.file_id` references `files.file_id`.
8. pgvector chunks contain their actual code content.
9. Neo4j stores structural relationships.
10. Source lookup is asymmetric depending on the originating store.
11. The local repository clone acts as the source of truth for source-storage reads.
12. Ingestion is deterministic except for embedding generation.
13. LLM reasoning happens at query time.
14. Query results are normalized and deduplicated before synthesis.

---

# 25. Future Improvements

The specifications identify several areas for future implementation decisions:

* Incremental ingestion using `content_hash`.
* Cleanup of stale chunks and Neo4j relationships.
* Better handling of malformed source files.
* Surfacing unresolved dependencies.
* Stronger transaction boundaries.
* Additional programming-language support.
* Multi-agent result reconciliation.
* Retrieval ranking/fusion across stores.
* Repository/source-storage staleness detection.
* Query latency benchmarking and parallel store retrieval.

---

## License

This project is intended as an AI-powered software engineering research and development system.
