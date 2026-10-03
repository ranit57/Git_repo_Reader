from typing import Any

from neo4j import GraphDatabase


class Neo4jClient:
    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
    ):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connection(self) -> None:
        self.driver.verify_connectivity()

    def upsert_symbol(self, symbol: Any) -> None:
        label = (
            "Function"
            if symbol.kind in {"function", "method"}
            else "Class"
        )

        query = f"""
        MERGE (s:{label} {{symbol_id: $symbol_id}})
        SET
            s.name = $name,
            s.file_path = $file_path,
            s.file_id = $file_id,
            s.start_line = $start_line,
            s.end_line = $end_line
        """

        with self.driver.session() as session:
            session.run(
                query,
                symbol_id=symbol.symbol_id,
                name=symbol.name,
                file_path=symbol.file_path,
                file_id=symbol.file_id,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
            )

    def upsert_file(self, file_id: str, path: str) -> None:
        query = """
        MERGE (f:File {file_id: $file_id})
        SET f.file_path = $path
        """

        with self.driver.session() as session:
            session.run(
                query,
                file_id=file_id,
                path=path,
            )

    def upsert_relationship(
        self,
        source_symbol_id: str,
        target_symbol_id: str,
        relationship_type: str,
    ) -> None:
        allowed = {
            "CALLS",
            "IMPORTS",
            "INHERITS",
            "CALLS_EXTERNAL",
        }

        if relationship_type not in allowed:
            raise ValueError(
                f"Unsupported relationship: {relationship_type}"
            )

        query = f"""
        MATCH (source {{symbol_id: $source_id}})
        MATCH (target {{symbol_id: $target_id}})
        MERGE (source)-[:{relationship_type}]->(target)
        """

        with self.driver.session() as session:
            session.run(
                query,
                source_id=source_symbol_id,
                target_id=target_symbol_id,
            )

    def upsert_package(
        self,
        name: str,
        version: str | None,
    ) -> None:
        query = """
        MERGE (p:Package {name: $name})
        SET
            p.symbol_id = $symbol_id,
            p.version = $version
        """

        with self.driver.session() as session:
            session.run(
                query,
                name=name,
                symbol_id=f"package:{name}",
                version=version,
            )

    def find_relationships(
        self,
        symbol_id: str,
        relationship_type: str | None = None,
    ) -> list[dict]:
        if relationship_type:
            allowed = {
                "CALLS",
                "IMPORTS",
                "INHERITS",
                "CALLS_EXTERNAL",
            }

            if relationship_type not in allowed:
                raise ValueError(
                    f"Unsupported relationship: {relationship_type}"
                )

            rel_pattern = f":{relationship_type}"
        else:
            rel_pattern = ""

        query = f"""
        MATCH (source {{symbol_id: $symbol_id}})
              -[r{rel_pattern}]->(target)
        RETURN
            source.symbol_id AS source_symbol_id,
            type(r) AS relationship,
            target.symbol_id AS target_symbol_id,
            target.name AS target_name
        """

        with self.driver.session() as session:
            return [
                record.data()
                for record in session.run(
                    query,
                    symbol_id=symbol_id,
                )
            ]

    def find_callers(self, symbol_id: str) -> list[dict]:
        query = """
        MATCH (caller)-[:CALLS]->(target {symbol_id: $symbol_id})
        RETURN
            caller.symbol_id AS symbol_id,
            caller.name AS name,
            caller.file_path AS file_path
        """

        with self.driver.session() as session:
            return [
                record.data()
                for record in session.run(
                    query,
                    symbol_id=symbol_id,
                )
            ]
