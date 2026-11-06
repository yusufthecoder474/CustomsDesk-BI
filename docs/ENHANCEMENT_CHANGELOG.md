# Enhancement scope

Original source and data are retained. Historical reports are under reports/archive/original; original README is there too. New executions are under reports/enhancement. No supplied Git directory was present. Original ZIPs remain unchanged. No remote repository was updated.

SupplySight: added study.py and capacity.py, tests and workbook additions; modified five notebooks for split workspace/Volume paths and client runtime logging, added the Volume storage branch, and extended the local notebook runner with an output root argument. Existing baseline forecasters and Gold schemas are unchanged. Workbook tests now accept the two requested new tabs.

CustomsDesk: added dashboard.py, response-band M transformation, SQL target contexts and relationship tests; existing 22 DAX definitions and warehouse schemas are unchanged. Default setup now preserves existing passwords; explicit rotation remains available. The existing rotation test now explicitly requests rotation; added tests cover preservation. Nonempty DATABASE_URL is retained and dedicated-container setup stops with a CLI instruction instead of blanking it. No local database credentials or Docker volumes were accessed or modified here.
