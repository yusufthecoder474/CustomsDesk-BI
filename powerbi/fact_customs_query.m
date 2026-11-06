// SYNTHETIC DATA. Additional response bands support the requested distribution visual.
let
    Source = fxLoad("fact_customs_query"),
    WithBand = Table.AddColumn(Source, "response_bucket", each
        if [response_hours] = null then "Not responded"
        else if [response_hours] <= 24 then "01: 0–24h"
        else if [response_hours] <= 48 then "02: >24–48h"
        else if [response_hours] <= 72 then "03: >48–72h"
        else "04: >72h", type text)
in WithBand
