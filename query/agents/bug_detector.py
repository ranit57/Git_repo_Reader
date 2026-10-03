from models.types import QueryResult
from query.agents.base_agent import BaseAgent


class BugDetector(BaseAgent):
    def retrieve(self, query: str, repo_id: str) -> list[QueryResult]:
        results = self.semantic_search(query, repo_id)

        # Use graph relationships to trace possible causes.
        return self.enrich_relationships(results)
