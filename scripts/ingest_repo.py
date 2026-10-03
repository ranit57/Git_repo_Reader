import argparse

from config.settings import settings
from ingestion.cloner import RepositoryCloner
from ingestion.embedding import EmbeddingModel
from ingestion.orchestrator import IngestionOrchestrator
from storage.neo4j_client import Neo4jClient
from storage.postgres_client import PostgresClient


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a Git repository"
    )
    parser.add_argument(
        "repo_url",
        help="GitHub repository URL",
    )

    args = parser.parse_args()

    postgres = PostgresClient(settings.postgres_url)

    neo4j = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
    )

    # Initialize embedder with explicit keyword args (model and base_url)
    embedder = EmbeddingModel(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )

    cloner = RepositoryCloner(
        settings.clone_base_dir
    )

    repo_id = cloner.repo_id_from_url(
        args.repo_url
    )

    repo_path = cloner.clone(
        args.repo_url,
        repo_id,
    )

    orchestrator = IngestionOrchestrator(
        postgres=postgres,
        neo4j=neo4j,
        embedder=embedder,
    )

    orchestrator.run(
        repo_path,
        repo_id,
    )

    print(
        f"Successfully ingested: {repo_id}"
    )

    postgres.close()
    neo4j.close()


if __name__ == "__main__":
    main()