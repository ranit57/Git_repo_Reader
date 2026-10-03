from ingestion.dependency_builder import DependencyBuilder
from models.types import Dependency, Edge


def test_resolves_external_dependency():
    edge = Edge(
        source_symbol_id="demo:payment.py:process_payment",
        edge_type="CALLS",
        target="stripe.charge",
        resolved=False,
    )

    dependencies = [
        Dependency(
            name="stripe",
            version="5.4.0",
        )
    ]

    result = DependencyBuilder().resolve(
        [edge],
        dependencies,
    )

    assert len(result) == 1
    assert result[0].resolved is True
    assert result[0].package_name == "stripe"
    assert result[0].package_version == "5.4.0"
    assert result[0].edge_type == "CALLS_EXTERNAL"


def test_keeps_unknown_dependency_unresolved():
    edge = Edge(
        source_symbol_id="demo:app.py:run",
        edge_type="CALLS",
        target="unknown.call",
        resolved=False,
    )

    result = DependencyBuilder().resolve(
        [edge],
        [],
    )

    assert len(result) == 1
    assert result[0].resolved is False