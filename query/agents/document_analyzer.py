import re

from models.types import QueryResult
from query.agents.base_agent import BaseAgent


class DocumentAnalyzer(BaseAgent):
    def retrieve(self, query: str, repo_id: str) -> list[QueryResult]:
        text = query.lower()
        explicit_file = self._explicit_file_result(query, repo_id)

        if any(word in text for word in ("file", "files", "folder", "folders", "structure", "tree")):
            explicit_results = [explicit_file] if explicit_file else []
            return [
                *explicit_results,
                *self.file_search(repo_id),
                *self.semantic_search(query, repo_id),
            ]

        if explicit_file:
            return [
                explicit_file,
                *self.semantic_search(query, repo_id),
            ]

        return self.semantic_search(query, repo_id)

    def _explicit_file_result(
        self,
        query: str,
        repo_id: str,
    ) -> QueryResult | None:
        for candidate in self._candidate_paths(query):
            result = self.file_path_search(repo_id, candidate)
            if result:
                return result

        return None

    @staticmethod
    def _candidate_paths(query: str) -> list[str]:
        if ".git/" in query.replace("\\", "/"):
            return []

        candidates = re.findall(r"`([^`]+)`", query)
        candidates.extend(
            re.findall(r"(?<!\S)[\w./-]+\.[A-Za-z0-9]+(?:/[^\s`]+)?", query)
        )

        seen = set()
        unique = []
        for candidate in candidates:
            normalized = candidate.strip().strip(".,:;")
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)

        return unique
