# Fresh-package verification

Executed after extracting CustomsDesk-BI.zip into a separate temporary directory:

- ZIP CRC validation: passed.
- Extracted test suite: **43 passed, 0 failed, 1 skipped** (PostgreSQL unavailable).
- Built and installed a regular Python wheel outside the source directory: passed.
- Ran the installed package against the full extracted synthetic input set: SUCCESS.
- Source checksum and all SQL KPI values matched the original verified run exactly.
- Packaged SQL resource was available from the installed wheel.

Commands executed:

```sh
python -m pytest -q --tb=short --junitxml=/tmp/customsdesk-extracted-tests.xml
python -m pip install --no-deps --no-build-isolation --target /tmp/customsdesk-final-install .
PYTHONPATH=/tmp/customsdesk-final-install python -m customsdesk.cli etl --data /tmp/customsdesk-final-check/CustomsDesk-BI/data/sample --database-url sqlite:////tmp/customsdesk-packaged.db --reports /tmp/customsdesk-package-reports
```

No PostgreSQL, Docker, M/DAX engine or Power BI Desktop execution is implied by these checks.
