from pathlib import Path

from ingestion.file_analyzer import FileAnalyzer


def test_python_file_is_source(tmp_path: Path):
    file = tmp_path / "app.py"
    file.write_text("def hello():\n    return 'hi'\n")

    records = FileAnalyzer().analyze(tmp_path)

    assert len(records) == 1
    assert records[0].language == "python"
    assert records[0].file_type == "source"
    assert records[0].loc == 2


def test_requirements_is_config(tmp_path: Path):
    file = tmp_path / "requirements.txt"
    file.write_text("fastapi==0.115.0\n")

    records = FileAnalyzer().analyze(tmp_path)

    assert records[0].file_type == "config"


def test_test_directory_is_test(tmp_path: Path):
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    file = test_dir / "test_app.py"
    file.write_text("def test_hello():\n    pass\n")

    records = FileAnalyzer().analyze(tmp_path)

    assert records[0].file_type == "test"


def test_ignores_git_directory(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    config = git_dir / "config"
    config.write_text("[remote]\n")

    records = FileAnalyzer().analyze(tmp_path)

    assert records == []
