// SYNTHETIC DATA. Not yet verified in Power BI Desktop.
(name as text) as table =>
let
    Allowed = {"dim_date","dim_country","dim_part","dim_authority","dim_query_type","fact_shipment","fact_customs_query","data_quality_results","etl_run_log","rejected_records","vw_kpis","vw_monthly","vw_authority","vw_country","vw_backlog","vw_query_detail"},
    SafeName = if List.Contains(Allowed, name) then name else error "Unknown warehouse object",
    Raw = if SourceMode = "PostgreSQL" then PostgreSQL.Database(Server, Database){[Schema="public",Item=SafeName]}[Data]
          else if SourceMode = "CSV" then Table.PromoteHeaders(Csv.Document(File.Contents(ExportFolder & "\" & SafeName & ".csv"), [Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]), [PromoteAllScalars=true])
          else error "SourceMode must be CSV or PostgreSQL",
    Trimmed = Table.TransformColumns(Raw, List.Transform(Table.ColumnNames(Raw), (c) => {c, (v) => if Value.Is(v, type text) then Text.Trim(v) else v})),
    Nulls = Table.ReplaceValue(Trimmed, "", null, Replacer.ReplaceValue, Table.ColumnNames(Trimmed)),
    DateCols = List.Intersect({Table.ColumnNames(Nulls), {"date_key","dispatch_date","expected_arrival_date","actual_arrival_date","opened_date","closed_date","review_date"}}),
    Dates = Table.TransformColumnTypes(Nulls, List.Transform(DateCols, each {_,type date}), "en-US"),
    TimeCols = List.Intersect({Table.ColumnNames(Dates), {"opened_at","assigned_at","responded_at","closed_at","started_at","finished_at","as_of"}}),
    UTC = Table.TransformColumns(Dates, List.Transform(TimeCols, (c) => {c, (v) => if v = null then null else DateTimeZone.RemoveZone(DateTimeZone.SwitchZone(DateTimeZone.FromText(Text.From(v)), 0)), type nullable datetime})),
    IntCols0 = List.Intersect({Table.ColumnNames(UTC), {"year","month","quantity","classification_version","sla_breach","source_rows","accepted","rejected","duplicates","superseded","row_number","id","response_within_sla","is_backlog"}}),
    IntCols = if SafeName = "vw_monthly" then List.RemoveItems(IntCols0,{"month"}) else IntCols0,
    Integers = Table.TransformColumnTypes(UTC,List.Transform(IntCols,each {_,Int64.Type}),"en-US"),
    NumberCols = List.Intersect({Table.ColumnNames(Integers), {"declared_value","sla_hours","response_hours","business_response_hours","backlog_hours","execution_seconds","total_shipments","total_queries","open_queries","avg_response_hours","median_response_hours","avg_business_response_days","sla_compliance_pct","sla_breaches","avg_backlog_hours","high_priority_unresolved","missing_classification_pct","invalid_classification_pct","dq_pass_rate_pct","queries","breaches","backlog","opened","closed","prior_closed","mom_throughput_pct"}}),
    Numbers = Table.TransformColumnTypes(Integers,List.Transform(NumberCols,each {_,type number}),"en-US"),
    BoolCols = List.Intersect({Table.ColumnNames(Numbers), {"review_required","is_weekday"}}),
    Flags = Table.TransformColumns(Numbers,List.Transform(BoolCols,(c) => {c, (v) => if v = null then null else if List.Contains({"true","1"},Text.Lower(Text.From(v))) then true else if List.Contains({"false","0"},Text.Lower(Text.From(v))) then false else error "Invalid boolean flag", type nullable logical})),
    TextCols = List.Intersect({Table.ColumnNames(Flags), {"shipment_id","supplier_id","part_id","query_id","authority_id","query_type","country_code","origin_country","destination_country","query_priority","query_status","code_state","run_id","classification_status","part_category","country_name","authority_name","age_bucket","source"}}),
    TextFields = Table.TransformColumnTypes(Flags,List.Transform(TextCols, each {_,type text})),
    // HS codes must remain text to preserve leading zeroes.
    Codes = if Table.HasColumns(TextFields, "hs_code") then Table.TransformColumnTypes(TextFields, {{"hs_code",type text}}) else TextFields
in
    Codes
