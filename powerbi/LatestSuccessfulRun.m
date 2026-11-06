// Connection-only scalar query; create before data_quality_results.
let
    Runs = fxLoad("etl_run_log"),
    Successful = Table.SelectRows(Runs, each [status] = "SUCCESS"),
    Sorted = Table.Sort(Successful, {{"finished_at",Order.Descending},{"run_id",Order.Descending}}),
    RunId = if Table.IsEmpty(Sorted) then error "No successful ETL run" else Sorted{0}[run_id]
in RunId
