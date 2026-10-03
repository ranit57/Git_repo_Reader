import argparse

from config.settings import settings
from ingestion.embedding import EmbeddingModel

from query.agents.bug_detector import BugDetector
from query.agents.code_navigator import CodeNavigator
from query.agents.document_analyzer import DocumentAnalyzer
from query.agents.retrieval_qa import RetrievalQA
from query.orchestrator import QueryOrchestrator
from query.source_lookup import SourceLookup
from query.synthesizer import Synthesizer

from storage.neo4j_client import Neo4jClient
from storage.postgres_client import PostgresClient


def main():
    parser = argparse.ArgumentParser(
        description="Query an ingested repository"
    )

    parser.add_argument(
        "repo_id",
        help="Repository ID",
    )

    parser.add_argument(
        "query",
        nargs="+",
        help="Question about the repository",
    )

    args = parser.parse_args()

    postgres = PostgresClient(
        settings.postgres_url
    )

    neo4j = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
    )

    # Local Ollama embeddings
    embedder = EmbeddingModel(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )

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

    # Groq LLM
    synthesizer = Synthesizer(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
    )

    orchestrator = QueryOrchestrator(
        agents=agents,
        source_lookup=SourceLookup(
            settings.clone_base_dir
        ),
        synthesizer=synthesizer,
    )

    question = " ".join(args.query)

    answer = orchestrator.run(question, args.repo_id)

    print("\n" + answer)

    postgres.close()
    neo4j.close()


if __name__ == "__main__":
    main()
