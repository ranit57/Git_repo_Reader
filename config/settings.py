import os
import tempfile
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    postgres_url: str
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str

    # Groq LLM
    groq_api_key: str
    groq_model: str

    # Local Ollama embeddings
    embedding_model: str
    embedding_dimensions: int
    ollama_base_url: str

    # Repository storage
    clone_base_dir: str

    # Retrieval
    pgvector_top_k: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            postgres_url=os.environ["POSTGRES_URL"],
            neo4j_uri=os.environ["NEO4J_URI"],
            neo4j_username=os.environ["NEO4J_USERNAME"],
            neo4j_password=os.environ["NEO4J_PASSWORD"],

            groq_api_key=os.environ["GROQ_API_KEY"],
            groq_model=os.getenv(
                "GROQ_MODEL",
                "llama-3.3-70b-versatile",
            ),

            embedding_model=os.getenv(
                "EMBEDDING_MODEL",
                "all-minilm",
            ),
            embedding_dimensions=int(
                os.getenv(
                    "EMBEDDING_DIMENSIONS",
                    "384",
                )
            ),
            ollama_base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            ),

            clone_base_dir=os.getenv(
                "CLONE_BASE_DIR",
                os.path.join(tempfile.gettempdir(), "repo-ai-engineer", "repos"),
            ),

            pgvector_top_k=int(
                os.getenv(
                    "PGVECTOR_TOP_K",
                    "10",
                )
            ),
        )


settings = Settings.from_env()