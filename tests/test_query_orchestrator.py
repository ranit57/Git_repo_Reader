from unittest.mock import Mock

from models.types import QueryResult
from query.orchestrator import QueryOrchestrator


def test_routes_bug_query():
    agent = Mock()

    agent.retrieve.return_value = [
        QueryResult(
            source="pgvector",
            symbol_id="demo:app.py:process",
            content="def process(): pass",
        )
    ]

    synthesizer = Mock()
    synthesizer.synthesize.return_value = (
        "Likely bug found."
    )

    orchestrator = QueryOrchestrator(
        agents={
            "bug_detector": agent,
            "code_navigator": agent,
        },
        source_lookup=Mock(
            resolve=lambda results, repo_id: results
        ),
        synthesizer=synthesizer,
    )

    answer = orchestrator.run(
        "Why is this bug failing?",
        "demo",
    )

    assert answer == "Likely bug found."
    agent.retrieve.assert_any_call(
        "Why is this bug failing?",
        "demo",
    )
    synthesizer.synthesize.assert_called_once()


def test_routes_file_query_to_document_analyzer():
    document_agent = Mock()
    document_agent.retrieve.return_value = [
        QueryResult(
            source="postgres",
            file_id="file-1",
            file_path="app.py",
        )
    ]

    synthesizer = Mock()
    synthesizer.synthesize.return_value = "Files listed."

    orchestrator = QueryOrchestrator(
        agents={
            "document_analyzer": document_agent,
        },
        source_lookup=Mock(
            resolve=lambda results, repo_id: results
        ),
        synthesizer=synthesizer,
    )

    answer = orchestrator.run(
        "Give details of files",
        "demo",
    )

    assert answer == "Files listed."
    document_agent.retrieve.assert_called_once_with(
        "Give details of files",
        "demo",
    )
