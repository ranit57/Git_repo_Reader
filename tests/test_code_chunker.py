from pathlib import Path

from ingestion.code_chunker import CodeChunker
from ingestion.shared_parser import SharedParser


def test_creates_function_chunk(tmp_path: Path):
    file = tmp_path / "app.py"
    file.write_text(
        "def hello():\n"
        "    return 'hi'\n"
    )

    parsed = SharedParser().parse(file, "python")

    chunks = CodeChunker().chunk(
        parsed,
        "file-1",
        "demo",
    )

    assert len(chunks) == 1
    assert chunks[0].symbol_id == (
        "demo:app.py:hello"
    )
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2
    assert "def hello" in chunks[0].content