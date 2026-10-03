import json
import re
from pathlib import Path

from models.types import Dependency


class ConfigAnalyzer:
    def analyze(self, path: Path) -> list[Dependency]:
        name = path.name.lower()

        if name == "requirements.txt":
            return self._requirements(path)

        if name == "package.json":
            return self._package_json(path)

        if name == "go.mod":
            return self._go_mod(path)

        if name == "pom.xml":
            return self._pom_xml(path)

        if name == "pyproject.toml":
            return self._pyproject(path)

        return []

    def _requirements(self, path: Path) -> list[Dependency]:
        dependencies = []

        for line in path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            match = re.match(
                r"^([A-Za-z0-9_.-]+)\s*"
                r"(?:==|>=|<=|~=|>|<)\s*([^\s;]+)",
                line,
            )

            if match:
                dependencies.append(
                    Dependency(
                        name=match.group(1),
                        version=match.group(2),
                    )
                )
            else:
                package = re.split(r"[<>=~!;]", line)[0].strip()

                if package:
                    dependencies.append(
                        Dependency(name=package)
                    )

        return dependencies

    def _package_json(self, path: Path) -> list[Dependency]:
        data = json.loads(
            path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )

        dependencies = []

        for section in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
        ):
            for name, version in data.get(
                section, {}
            ).items():
                dependencies.append(
                    Dependency(
                        name=name,
                        version=str(version),
                    )
                )

        return dependencies

    def _go_mod(self, path: Path) -> list[Dependency]:
        dependencies = []

        for line in path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():
            line = line.strip()

            if not line or line.startswith("//"):
                continue

            match = re.match(
                r"^([^\s]+)\s+([^\s]+)",
                line,
            )

            if match and (
                match.group(2).startswith("v")
            ):
                dependencies.append(
                    Dependency(
                        name=match.group(1),
                        version=match.group(2),
                    )
                )

        return dependencies

    def _pom_xml(self, path: Path) -> list[Dependency]:
        import xml.etree.ElementTree as ET

        root = ET.parse(path).getroot()

        dependencies = []

        for dependency in root.iter():
            if not dependency.tag.endswith(
                "dependency"
            ):
                continue

            group_id = None
            artifact_id = None
            version = None

            for child in dependency:
                tag = child.tag.split("}")[-1]

                if tag == "groupId":
                    group_id = child.text
                elif tag == "artifactId":
                    artifact_id = child.text
                elif tag == "version":
                    version = child.text

            if artifact_id:
                name = (
                    f"{group_id}:{artifact_id}"
                    if group_id
                    else artifact_id
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                    )
                )

        return dependencies

    def _pyproject(self, path: Path) -> list[Dependency]:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        data = tomllib.loads(
            path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )

        dependencies = []

        project = data.get("project", {})

        for dependency in project.get(
            "dependencies", []
        ):
            name = re.split(
                r"[<>=!~;\[]",
                dependency,
                maxsplit=1,
            )[0].strip()

            version_match = re.search(
                r"(?:==|>=|<=|~=|>|<)\s*([^\s;]+)",
                dependency,
            )

            dependencies.append(
                Dependency(
                    name=name,
                    version=(
                        version_match.group(1)
                        if version_match
                        else None
                    ),
                )
            )

        return dependencies