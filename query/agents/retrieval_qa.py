from models.types import QueryResult
from query.agents.base_agent import BaseAgent


class RetrievalQA(BaseAgent):
    def retrieve(self, query: str, repo_id: str) -> list[QueryResult]:
        # pgvector is the primary source for grounded code answers.
        return self.semantic_search(query, repo_id)
