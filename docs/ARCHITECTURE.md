# Architecture

SYNTHETIC DATA only. This is an independent student project without Volvo affiliation.

```mermaid
flowchart TD
  A["Shipment CSV"] --> D["Raw audit and checksums"]
  B["Customs queries JSON"] --> D
  C["Part master CSV"] --> D
  D --> E["Validation and normalization"]
  E --> F["Quarantine with reasons"]
  E --> G["Atomic warehouse snapshot"]
  G --> H["SQL KPIs and exports"]
  H --> I["Power Query and DAX"]
  I --> J["Three Power BI pages"]
  G --> K["KPI baseline and change trials"]
  K --> L["Regression differences"]
```

```mermaid
erDiagram
  dim_part ||--o{ fact_shipment : classifies
  dim_part ||--o{ fact_customs_query : concerns
  dim_country ||--o{ fact_shipment : origin_destination
  dim_country ||--o{ fact_customs_query : shipment_origin
  dim_date ||--o{ fact_shipment : dispatch
  dim_date ||--o{ fact_customs_query : opened
  dim_authority ||--o{ fact_customs_query : handles
  dim_query_type ||--o{ fact_customs_query : categorizes
  fact_shipment ||--o{ fact_customs_query : references
```

The SQL foreign key between query and shipment enforces source integrity. Do **not** create that
fact-to-fact relationship in Power BI: use shared dimensions and single-direction filters instead.
Shipment grain: one accepted shipment ID. Query grain: one accepted query ID. Part grain: one current
accepted part ID/version. This prevents multiplying shipment values by the number of queries.

Python: deterministic generators, validation, business-calendar overlap, orchestration and export.
SQL: persisted facts/dimensions, integrity constraints, aggregation, median window, monthly LAG.
PostgreSQL is the deployment target. SQLite is an explicitly labeled local fallback, not evidence
of PostgreSQL execution. M and DAX are supplied source; Power BI Desktop verification remains pending.
