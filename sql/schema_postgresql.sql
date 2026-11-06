-- SYNTHETIC DATA warehouse; generated from SQLAlchemy metadata.


CREATE TABLE change_request_log (
	change_id VARCHAR(100) NOT NULL, 
	scenario VARCHAR(100), 
	status VARCHAR(100), 
	details TEXT, 
	PRIMARY KEY (change_id)
)

;


CREATE TABLE dim_authority (
	authority_id VARCHAR(100) NOT NULL, 
	authority_name VARCHAR(100), 
	PRIMARY KEY (authority_id)
)

;


CREATE TABLE dim_country (
	country_code VARCHAR(100) NOT NULL, 
	country_name VARCHAR(100), 
	PRIMARY KEY (country_code)
)

;


CREATE TABLE dim_date (
	date_key VARCHAR(100) NOT NULL, 
	year INTEGER, 
	month INTEGER, 
	is_weekday BOOLEAN, 
	PRIMARY KEY (date_key)
)

;


CREATE TABLE dim_part (
	part_id VARCHAR(100) NOT NULL, 
	part_description TEXT, 
	part_category VARCHAR(100), 
	hs_code VARCHAR(100), 
	classification_status VARCHAR(100), 
	classification_version INTEGER NOT NULL, 
	review_date VARCHAR(100), 
	review_required BOOLEAN NOT NULL, 
	code_state VARCHAR(100) NOT NULL, 
	PRIMARY KEY (part_id), 
	CHECK (classification_version > 0), 
	CHECK (code_state IN ('VALID','MISSING','INVALID'))
)

;


CREATE TABLE dim_query_type (
	query_type VARCHAR(100) NOT NULL, 
	PRIMARY KEY (query_type)
)

;


CREATE TABLE etl_run_log (
	run_id VARCHAR(100) NOT NULL, 
	status VARCHAR(100), 
	started_at VARCHAR(100), 
	finished_at VARCHAR(100), 
	as_of VARCHAR(100), 
	checksum VARCHAR(100), 
	execution_seconds FLOAT, 
	error TEXT, 
	PRIMARY KEY (run_id)
)

;


CREATE TABLE data_quality_results (
	id SERIAL NOT NULL, 
	run_id VARCHAR(100) NOT NULL, 
	source VARCHAR(100), 
	source_rows INTEGER, 
	accepted INTEGER, 
	rejected INTEGER, 
	duplicates INTEGER, 
	superseded INTEGER, 
	source_checksum VARCHAR(100), 
	PRIMARY KEY (id), 
	UNIQUE (run_id, source), 
	FOREIGN KEY(run_id) REFERENCES etl_run_log (run_id)
)

;


CREATE TABLE fact_shipment (
	shipment_id VARCHAR(100) NOT NULL, 
	supplier_id VARCHAR(100) NOT NULL, 
	part_id VARCHAR(100) NOT NULL, 
	origin_country VARCHAR(100) NOT NULL, 
	destination_country VARCHAR(100) NOT NULL, 
	dispatch_date VARCHAR(100) NOT NULL, 
	expected_arrival_date VARCHAR(100), 
	actual_arrival_date VARCHAR(100), 
	shipment_status VARCHAR(100) NOT NULL, 
	declared_value FLOAT NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (shipment_id), 
	CHECK (quantity > 0 AND declared_value >= 0), 
	CHECK (shipment_status IN ('DISPATCHED','IN_TRANSIT','ARRIVED')), 
	FOREIGN KEY(part_id) REFERENCES dim_part (part_id), 
	FOREIGN KEY(origin_country) REFERENCES dim_country (country_code), 
	FOREIGN KEY(destination_country) REFERENCES dim_country (country_code), 
	FOREIGN KEY(dispatch_date) REFERENCES dim_date (date_key)
)

;

CREATE INDEX ix_shipment_part ON fact_shipment (part_id);


CREATE TABLE kpi_snapshot (
	snapshot_id VARCHAR(100) NOT NULL, 
	run_id VARCHAR(100) NOT NULL, 
	label VARCHAR(100), 
	payload TEXT, 
	PRIMARY KEY (snapshot_id), 
	FOREIGN KEY(run_id) REFERENCES etl_run_log (run_id)
)

;


CREATE TABLE raw_records (
	id SERIAL NOT NULL, 
	run_id VARCHAR(100) NOT NULL, 
	source VARCHAR(100), 
	row_number INTEGER, 
	payload TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (run_id, source, row_number), 
	FOREIGN KEY(run_id) REFERENCES etl_run_log (run_id)
)

;


CREATE TABLE rejected_records (
	id SERIAL NOT NULL, 
	run_id VARCHAR(100) NOT NULL, 
	source VARCHAR(100), 
	row_number INTEGER, 
	reason TEXT, 
	payload TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES etl_run_log (run_id)
)

;


CREATE TABLE fact_customs_query (
	query_id VARCHAR(100) NOT NULL, 
	shipment_id VARCHAR(100) NOT NULL, 
	authority_id VARCHAR(100) NOT NULL, 
	query_type VARCHAR(100) NOT NULL, 
	country_code VARCHAR(100) NOT NULL, 
	opened_date VARCHAR(100) NOT NULL, 
	part_id VARCHAR(100) NOT NULL, 
	closed_date VARCHAR(100), 
	opened_at VARCHAR(100), 
	assigned_at VARCHAR(100), 
	responded_at VARCHAR(100), 
	closed_at VARCHAR(100), 
	query_priority VARCHAR(100), 
	query_status VARCHAR(100), 
	assigned_team VARCHAR(100), 
	response_outcome VARCHAR(100), 
	opened_month VARCHAR(100), 
	closed_month VARCHAR(100), 
	age_bucket VARCHAR(100), 
	sla_hours FLOAT NOT NULL, 
	response_hours FLOAT, 
	business_response_hours FLOAT, 
	backlog_hours FLOAT, 
	sla_breach INTEGER NOT NULL, 
	PRIMARY KEY (query_id), 
	CHECK (sla_hours > 0), 
	CHECK (sla_breach IN (0,1)), 
	CHECK (response_hours IS NULL OR response_hours >= 0), 
	CHECK (query_status IN ('OPEN','ASSIGNED','RESPONDED','CLOSED')), 
	CHECK (query_priority IN ('HIGH','NORMAL','LOW')), 
	FOREIGN KEY(shipment_id) REFERENCES fact_shipment (shipment_id), 
	FOREIGN KEY(authority_id) REFERENCES dim_authority (authority_id), 
	FOREIGN KEY(query_type) REFERENCES dim_query_type (query_type), 
	FOREIGN KEY(country_code) REFERENCES dim_country (country_code), 
	FOREIGN KEY(opened_date) REFERENCES dim_date (date_key), 
	FOREIGN KEY(part_id) REFERENCES dim_part (part_id)
)

;

CREATE INDEX ix_query_shipment ON fact_customs_query (shipment_id);

CREATE INDEX ix_query_opened ON fact_customs_query (opened_date);

CREATE INDEX ix_query_authority_status ON fact_customs_query (authority_id, query_status);