from sqlalchemy import text

from customsdesk.measure_sql import SQL
from customsdesk.pipeline import run


def test_all_raw_table_reference_queries_execute(db, source, tmp_path):
    run(db, source, tmp_path / "reports")
    assert len(SQL) == 22
    with db.connect() as conn:
        results = {name: conn.scalar(text(query)) for name, query in SQL.items()}
        assert results["Total Queries"] == conn.scalar(
            text("SELECT COUNT(query_id) FROM fact_customs_query")
        )
        assert results["Open Backlog"] >= results["High Priority Unresolved"]
        assert 0 <= results["SLA Compliance %"] <= 1
        assert all("vw_" not in query for query in SQL.values())
