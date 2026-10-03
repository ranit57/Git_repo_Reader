import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4


class RepositoryCloner:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def clone(self, repo_url: str, repo_id: str) -> Path:
        repo_url = self._normalize_repo_url(repo_url)
        target = self.base_dir / repo_id
        temp_target = self.base_dir / f"{repo_id}-{uuid4().hex}"

        if target.exists():
            self._remove_tree(target)

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_target)],
                check=True,
                capture_output=True,
                text=True,
            )
            if target.exists():
                self._remove_tree(target)
            temp_target.rename(target)
        except subprocess.CalledProcessError as exc:
            self._remove_tree(temp_target)
            raise RuntimeError(
                f"Failed to clone repository: {exc.stderr.strip()}"
            ) from exc
        except Exception:
            self._remove_tree(temp_target)
            raise

        return target

    def _remove_tree(self, path: Path) -> None:
        if not path.exists():
            return

        def onerror(func, path_str, exc_info):
            try:
                os.chmod(path_str, 0o700)
                func(path_str)
            except Exception:
                raise

        shutil.rmtree(path, onerror=onerror)

    @staticmethod
    def _normalize_repo_url(repo_url: str) -> str:
        parsed = urlparse(repo_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid repository URL")

        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def repo_id_from_url(repo_url: str) -> str:
        path = urlparse(repo_url).path.rstrip("/")
        name = Path(path).name

        if name.endswith(".git"):
            name = name[:-4]

        if not name:
            raise ValueError("Invalid repository URL")

        return name