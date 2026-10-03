from pathlib import Path

from ingestion.ast_parser import ASTParser
from ingestion.shared_parser import SharedParser


def test_extracts_function(tmp_path: Path):
    file = tmp_path / "app.py"
    file.write_text(
        "def hello():\n"
        "    return 'hi'\n"
    )

    parsed = SharedParser().parse(file, "python")

    result = ASTParser().parse(
        parsed,
        "demo",
        "file-1",
    )

    assert len(result.symbols) == 1
    assert result.symbols[0].name == "hello"
    assert result.symbols[0].kind == "function"


def test_extracts_call(tmp_path: Path):
    file = tmp_path / "app.py"
    file.write_text(
        "def save():\n"
        "    pass\n\n"
        "def process():\n"
        "    save()\n"
    )

    parsed = SharedParser().parse(file, "python")

    result = ASTParser().parse(
        parsed,
        "demo",
        "file-1",
    )

    calls = [
        edge
        for edge in result.edges
        if edge.edge_type == "CALLS"
    ]

    assert calls
    assert any(edge.target == "save" for edge in calls)