from unittest.mock import Mock

from query.agents.document_analyzer import DocumentAnalyzer


def test_file_queries_include_file_metadata_before_semantic_results():
    postgres = Mock()
    postgres.list_files.return_value = [
        {
            "file_id": "file-1",
            "path": "app.py",
            "language": "python",
            "file_type": "source",
            "loc": 10,
        }
    ]
    postgres.search_chunks.return_value = []

    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    results = DocumentAnalyzer(
        postgres,
        Mock(),
        embedder,
    ).retrieve("show files", "demo")

    assert results[0].source == "postgres"
    assert results[0].file_path == "app.py"
    postgres.search_chunks.assert_called_once()


def test_explicit_file_query_loads_file_lines():
    postgres = Mock()
    postgres.get_file.return_value = {
        "file_id": "file-1",
        "path": "README.md",
        "language": None,
        "file_type": "doc",
        "loc": 4,
    }
    postgres.list_files.return_value = []
    postgres.search_chunks.return_value = []

    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    results = DocumentAnalyzer(
        postgres,
        Mock(),
        embedder,
    ).retrieve("show me `README.md` file", "demo")

    assert results[0].file_path == "README.md"
    assert results[0].start_line == 1
    assert results[0].end_line == 4


def test_git_config_query_is_not_loaded():
    postgres = Mock()
    postgres.list_files.return_value = []
    postgres.search_chunks.return_value = []

    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    DocumentAnalyzer(
        postgres,
        Mock(),
        embedder,
    ).retrieve("show me `.git/config` file", "demo")

    postgres.get_file.assert_not_called()
