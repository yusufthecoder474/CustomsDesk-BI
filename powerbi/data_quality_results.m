// Only the latest successful run; avoids double counting repeated ETL runs.
let
    Source = fxLoad("data_quality_results"),
    Latest = Table.SelectRows(Source, each [run_id] = LatestSuccessfulRun)
in Latest
