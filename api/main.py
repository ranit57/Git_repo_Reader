from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingest_routes import create_router as create_ingest_router
from api.job_runner import JobRunner
from api.query_routes import create_router as create_query_router
from config.settings import settings
from ingestion.cloner import RepositoryCloner
from ingestion.embedding import EmbeddingModel
from ingestion.orchestrator import IngestionOrchestrator

from query.agents.bug_detector import BugDetector
from query.agents.code_navigator import CodeNavigator
from query.agents.document_analyzer import DocumentAnalyzer
from query.agents.retrieval_qa import RetrievalQA
from query.orchestrator import QueryOrchestrator
from query.source_lookup import SourceLookup
from query.synthesizer import Synthesizer

from storage.neo4j_client import Neo4jClient
from storage.postgres_client import PostgresClient


app = FastAPI(
    title="Repo AI Engineer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Storage
# -------------------------

postgres = PostgresClient(
    settings.postgres_url
)

neo4j = Neo4jClient(
    settings.neo4j_uri,
    settings.neo4j_username,
    settings.neo4j_password,
)


# -------------------------
# Local Ollama Embeddings
# -------------------------

embedder = EmbeddingModel(
    model=settings.embedding_model,
    base_url=settings.ollama_base_url,
)


# -------------------------
# Ingestion
# -------------------------

ingestion_orchestrator = IngestionOrchestrator(
    postgres=postgres,
    neo4j=neo4j,
    embedder=embedder,
)

cloner = RepositoryCloner(
    settings.clone_base_dir
)

job_runner = JobRunner(
    cloner=cloner,
    orchestrator=ingestion_orchestrator,
)


# -------------------------
# Query Agents
# -------------------------

agents = {
    "code_navigator": CodeNavigator(
        postgres,
        neo4j,
        embedder,
    ),
    "retrieval_qa": RetrievalQA(
        postgres,
        neo4j,
        embedder,
    ),
    "bug_detector": BugDetector(
        postgres,
        neo4j,
        embedder,
    ),
    "document_analyzer": DocumentAnalyzer(
        postgres,
        neo4j,
        embedder,
    ),
}


# -------------------------
# Groq Synthesizer
# -------------------------

synthesizer = Synthesizer(
    api_key=settings.groq_api_key,
    model=settings.groq_model,
)


query_orchestrator = QueryOrchestrator(
    agents=agents,
    source_lookup=SourceLookup(
        cloner.base_dir
    ),
    synthesizer=synthesizer,
)


# -------------------------
# Routes
# -------------------------

app.include_router(
    create_ingest_router(job_runner)
)

app.include_router(
    create_query_router(query_orchestrator)
)


@app.get("/health")
def health():
    return {"status": "ok"}