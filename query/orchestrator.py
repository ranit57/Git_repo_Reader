from models.types import QueryResult
from query.agents.base_agent import BaseAgent
from query.agents.bug_detector import BugDetector
from query.agents.code_navigator import CodeNavigator
from query.agents.document_analyzer import DocumentAnalyzer
from query.agents.retrieval_qa import RetrievalQA
from query.merge import ResultMerger
from query.source_lookup import SourceLookup
from query.synthesizer import Synthesizer


class QueryOrchestrator:
    def __init__(
        self,
        agents: dict[str, BaseAgent],
        source_lookup: SourceLookup,
        synthesizer: Synthesizer,
    ):
        self.agents = agents
        self.source_lookup = source_lookup
        self.merger = ResultMerger()
        self.synthesizer = synthesizer

    def run(self, query: str, repo_id: str) -> str:
        agent_names = self._route(query)

        results: list[QueryResult] = []

        for name in agent_names:
            agent = self.agents.get(name)

            if not agent:
                continue

            results.extend(agent.retrieve(query, repo_id))

        resolved = self.source_lookup.resolve(results, repo_id)
        merged = self.merger.merge(resolved)

        return self.synthesizer.synthesize(
            query,
            merged,
        )

    def _route(self, query: str) -> list[str]:
        text = query.lower()

        if any(
            word in text
            for word in (
                "bug",
                "error",
                "failure",
                "failing",
                "exception",
                "broken",
            )
        ):
            return ["bug_detector", "code_navigator"]

        if any(
            word in text
            for word in (
                "call",
                "caller",
                "dependency",
                "depends",
                "relationship",
                "defined",
                "structure",
            )
        ):
            return ["code_navigator"]

        if any(
            word in text
            for word in (
                "summarize",
                "summary",
                "explain file",
                "overview",
                "component",
                "file",
                "files",
                "folder",
                "folders",
                "tree",
            )
        ):
            return ["document_analyzer"]

        return ["retrieval_qa"]
