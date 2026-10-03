import hashlib
import mimetypes
from pathlib import Path

from models.types import FileRecord


LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
}

CONFIG_FILES = {
    "requirements.txt",
    "package.json",
    "pom.xml",
    "go.mod",
    "cargo.toml",
    "pyproject.toml",
    "gemfile",
    "composer.json",
}

DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".ipynb",
}

GENERATED_DIRS = {
    "vendor",
    "node_modules",
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
}

SUPPORTED_LANGUAGES = set(LANGUAGE_BY_EXTENSION.values())


class FileAnalyzer:
    def analyze(self, repo_path: Path) -> list[FileRecord]:
        records = []

        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue

            relative_path = path.relative_to(repo_path)

            if self._should_ignore(relative_path):
                continue

            record = self._analyze_file(
                repo_path,
                path,
                relative_path,
            )

            records.append(record)

        return records

    def _analyze_file(
        self,
        repo_path: Path,
        path: Path,
        relative_path: Path,
    ) -> FileRecord:
        content = self._read_file(path)
        language = self._detect_language(path, content)
        file_type = self._classify_file(
            relative_path,
            content,
            language,
        )
        return FileRecord(
            file_id=self._file_id(repo_path.name, relative_path),
            repo_id=repo_path.name,
            path=relative_path.as_posix(),
            language=language,
            file_type=file_type,
            loc=len(content.splitlines()),
            content_hash=self._content_hash(content),
        )

    def _should_ignore(self, relative_path: Path) -> bool:
        path_string = f"/{relative_path.as_posix().lower()}/"

        if any(
            f"/{directory}/" in path_string
            for directory in GENERATED_DIRS | IGNORED_DIRS
        ):
            return True

        if any(part.startswith(".") for part in relative_path.parts):
            return True

        return False

    @staticmethod
    def _read_file(path: Path) -> str:
        try:
            return path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read file: {path}"
            ) from exc

    def _detect_language(
        self,
        path: Path,
        content: str,
    ) -> str | None:
        language = LANGUAGE_BY_EXTENSION.get(
            path.suffix.lower()
        )

        if language:
            return language

        # Extensionless / ambiguous files: basic content sniffing.
        first_line = content.splitlines()[0] if content else ""

        if first_line.startswith("#!") and "python" in first_line:
            return "python"

        mime_type, _ = mimetypes.guess_type(path.name)

        if mime_type == "text/x-python":
            return "python"

        return None

    def _classify_file(
        self,
        relative_path: Path,
        content: str,
        language: str | None,
    ) -> str:
        path_string = f"/{relative_path.as_posix().lower()}/"
        filename = relative_path.name.lower()

        if any(
            f"/{directory}/" in path_string
            for directory in GENERATED_DIRS
        ):
            return "generated"

        if "@generated" in content:
            return "generated"

        if filename in CONFIG_FILES:
            return "config"

        # Simple document files (markdown, text, notebooks)
        if relative_path.suffix.lower() in DOC_EXTENSIONS:
            return "doc"

        if "/test/" in path_string or "/spec/" in path_string:
            return "test"

        if language in SUPPORTED_LANGUAGES:
            return "source"

        return "generated"

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha1(
            content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _file_id(repo_id: str, relative_path: Path) -> str:
        """Create a deterministic id scoped to the repository and path.

        This avoids collisions when different repositories have the same
        relative paths (e.g., README.md).
        """
        digest = hashlib.sha1(
            f"{repo_id}:{relative_path.as_posix()}".encode("utf-8")
        ).hexdigest()

        return digest[:32]
