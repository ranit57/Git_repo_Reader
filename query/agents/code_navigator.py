from models.types import QueryResult
from query.agents.base_agent import BaseAgent


class CodeNavigator(BaseAgent):
    def retrieve(self, query: str, repo_id: str) -> list[QueryResult]:
        results = self.semantic_search(query, repo_id)

        enriched = self.enrich_relationships(results)

        return enriched
