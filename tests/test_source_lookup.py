from pathlib import Path

from models.types import QueryResult
from query.source_lookup import SourceLookup


def test_loads_source_from_repo_specific_clone(tmp_path: Path):
    repo_dir = tmp_path / "demo"
    repo_dir.mkdir()
    source = repo_dir / "app.py"
    source.write_text(
        "line 1\n"
        "line 2\n"
        "line 3\n",
        encoding="utf-8",
    )

    result = QueryResult(
        source="postgres",
        file_path="app.py",
        start_line=2,
        end_line=3,
    )

    resolved = SourceLookup(tmp_path).resolve([result], "demo")

    assert resolved[0].content == "line 2\nline 3"
