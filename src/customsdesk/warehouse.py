"""SQLAlchemy warehouse, PostgreSQL primary; SQLite explicit development fallback."""
from sqlalchemy import (MetaData,Table,Column,String,Integer,Float,Boolean,Text,ForeignKey,CheckConstraint,UniqueConstraint,Index,create_engine,event,text)
metadata=MetaData()
def table(name,*cols): return Table(name,metadata,*cols)
def col(name,kind=String(100),**kw): return Column(name,kind,**kw)
def key(name): return col(name,primary_key=True)
def fk(name,target): return Column(name,String(100),ForeignKey(target),nullable=False)
dim_date=table("dim_date",key("date_key"),col("year",Integer),col("month",Integer),col("is_weekday",Boolean))
dim_country=table("dim_country",key("country_code"),col("country_name"))
dim_authority=table("dim_authority",key("authority_id"),col("authority_name"))
dim_query_type=table("dim_query_type",key("query_type"))
dim_part=table("dim_part",key("part_id"),col("part_description",Text),col("part_category"),col("hs_code"),col("classification_status"),col("classification_version",Integer,nullable=False),col("review_date"),col("review_required",Boolean,nullable=False),col("code_state",nullable=False),CheckConstraint("classification_version > 0"),CheckConstraint("code_state IN ('VALID','MISSING','INVALID')"))
fact_shipment=table("fact_shipment",key("shipment_id"),col("supplier_id",nullable=False),fk("part_id","dim_part.part_id"),fk("origin_country","dim_country.country_code"),fk("destination_country","dim_country.country_code"),fk("dispatch_date","dim_date.date_key"),col("expected_arrival_date"),col("actual_arrival_date"),col("shipment_status",nullable=False),col("declared_value",Float,nullable=False),col("quantity",Integer,nullable=False),CheckConstraint("quantity > 0 AND declared_value >= 0"),CheckConstraint("shipment_status IN ('DISPATCHED','IN_TRANSIT','ARRIVED')"))
fact_customs_query=table("fact_customs_query",key("query_id"),fk("shipment_id","fact_shipment.shipment_id"),fk("authority_id","dim_authority.authority_id"),fk("query_type","dim_query_type.query_type"),fk("country_code","dim_country.country_code"),fk("opened_date","dim_date.date_key"),fk("part_id","dim_part.part_id"),col("closed_date"),*[col(n) for n in ["opened_at","assigned_at","responded_at","closed_at","query_priority","query_status","assigned_team","response_outcome","opened_month","closed_month","age_bucket"]],col("sla_hours",Float,nullable=False),col("response_hours",Float),col("business_response_hours",Float),col("backlog_hours",Float),col("sla_breach",Integer,nullable=False),CheckConstraint("sla_hours > 0"),CheckConstraint("sla_breach IN (0,1)"),CheckConstraint("response_hours IS NULL OR response_hours >= 0"),CheckConstraint("query_status IN ('OPEN','ASSIGNED','RESPONDED','CLOSED')"),CheckConstraint("query_priority IN ('HIGH','NORMAL','LOW')"))
Index("ix_query_opened",fact_customs_query.c.opened_date)
Index("ix_query_authority_status",fact_customs_query.c.authority_id,fact_customs_query.c.query_status)
Index("ix_query_shipment",fact_customs_query.c.shipment_id)
Index("ix_shipment_part",fact_shipment.c.part_id)
etl_run_log=table("etl_run_log",key("run_id"),col("status"),col("started_at"),col("finished_at"),col("as_of"),col("checksum"),col("execution_seconds",Float),col("error",Text))
raw_records=table("raw_records",Column("id",Integer,primary_key=True,autoincrement=True),fk("run_id","etl_run_log.run_id"),col("source"),col("row_number",Integer),col("payload",Text),UniqueConstraint("run_id","source","row_number"))
rejected_records=table("rejected_records",Column("id",Integer,primary_key=True,autoincrement=True),fk("run_id","etl_run_log.run_id"),col("source"),col("row_number",Integer),col("reason",Text),col("payload",Text))
data_quality_results=table("data_quality_results",Column("id",Integer,primary_key=True,autoincrement=True),fk("run_id","etl_run_log.run_id"),col("source"),*[col(n,Integer) for n in ["source_rows","accepted","rejected","duplicates","superseded"]],col("source_checksum"),UniqueConstraint("run_id","source"))
kpi_snapshot=table("kpi_snapshot",key("snapshot_id"),fk("run_id","etl_run_log.run_id"),col("label"),col("payload",Text))
change_request_log=table("change_request_log",key("change_id"),col("scenario"),col("status"),col("details",Text))

def engine(url,timeout=5):
    from sqlalchemy.engine import make_url
    dialect=make_url(url).get_backend_name()
    args={"connect_timeout":timeout} if dialect=="postgresql" else {"timeout":timeout}
    result=create_engine(url,connect_args=args,hide_parameters=True,pool_pre_ping=True)
    if result.dialect.name=="sqlite":
        @event.listens_for(result,"connect")
        def constraints(conn,_): conn.execute("PRAGMA foreign_keys=ON")
    return result

def initialize(db):
    metadata.create_all(db)
    from pathlib import Path
    sql=Path(__file__).with_name("views.sql")
    with db.begin() as conn:
        for statement in sql.read_text().split(";"):
            if statement.strip():
                if db.dialect.name == "postgresql": statement=statement.replace("CREATE VIEW IF NOT EXISTS", "CREATE OR REPLACE VIEW")
                conn.execute(text(statement))
