from dataclasses import dataclass

from models.types import Dependency, Edge


@dataclass
class ResolvedExternalEdge:
    from_symbol_id: str
    edge_type: str
    package_name: str
    package_version: str | None
    resolved: bool


class DependencyBuilder:
    def resolve(
        self,
        unresolved_edges: list[Edge],
        dependencies: list[Dependency],
    ) -> list[ResolvedExternalEdge]:
        dependency_map = {
            self._normalize(dep.name): dep
            for dep in dependencies
        }

        results = []

        for edge in unresolved_edges:
            package_name = self._find_package(
                edge.target,
                dependency_map,
            )

            if package_name is None:
                results.append(
                    ResolvedExternalEdge(
                        from_symbol_id=edge.source_symbol_id,
                        edge_type="CALLS_EXTERNAL",
                        package_name=edge.target,
                        package_version=None,
                        resolved=False,
                    )
                )
                continue

            dependency = dependency_map[package_name]

            results.append(
                ResolvedExternalEdge(
                    from_symbol_id=edge.source_symbol_id,
                    edge_type="CALLS_EXTERNAL",
                    package_name=dependency.name,
                    package_version=dependency.version,
                    resolved=True,
                )
            )

        return results

    def _find_package(
        self,
        target: str,
        dependency_map: dict[str, Dependency],
    ) -> str | None:
        normalized_target = self._normalize(target)

        # Exact package match.
        if normalized_target in dependency_map:
            return normalized_target

        # Match "stripe.charge" -> "stripe".
        parts = normalized_target.split(".")

        for index in range(
            len(parts),
            0,
            -1,
        ):
            candidate = ".".join(parts[:index])

            if candidate in dependency_map:
                return candidate

        return None

    @staticmethod
    def _normalize(name: str) -> str:
        return (
            name.strip()
            .lower()
            .replace("-", "_")
        )