"""Regenerate PostgreSQL DDL from the executable model (run at repository root)."""
from pathlib import Path
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable,CreateIndex
from customsdesk.warehouse import metadata
pieces=['-- SYNTHETIC DATA warehouse; generated from SQLAlchemy metadata.']
for table in metadata.sorted_tables:
    pieces.append(str(CreateTable(table).compile(dialect=postgresql.dialect()))+';')
    pieces.extend(str(CreateIndex(index).compile(dialect=postgresql.dialect()))+';' for index in table.indexes)
Path('sql/schema_postgresql.sql').write_text('\n\n'.join(pieces))
Path('sql/views_postgresql.sql').write_text(Path('sql/views.sql').read_text().replace('CREATE VIEW IF NOT EXISTS','CREATE OR REPLACE VIEW'))
