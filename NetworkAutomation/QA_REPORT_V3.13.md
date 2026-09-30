# QA REPORT - v3.13 Auto IP / Excel

Date: 2026-09-30
Runtime: Python 3.13.5 / Linux

## Results

- 34 automated tests: PASS.
- 11 original regression checks: PASS on a separate copy of the uploaded application.
- Tk UI smoke test: PASS (virtual display; no Tk callback exceptions).
- Simulated end-to-end run on a COPY of the uploaded legacy database: PASS.
- Original database and credential-key bytes in the delivery: unchanged from uploaded ZIP.
- Original feature modules: unchanged. main.py gains only imports/menu/page lifecycle/close handling.
- Excel template: input read-back and rendered layout checked; no formulas or macros.

## New-test coverage

IP parsing, canonical IPv6, duplicates, invalid/multicast/CIDR/scope rejection,
Excel headers including Vietnamese aliases, formulas rejected, invalid batches not saved,
role/authorization checks, limits, missing-profile preflight, encrypted community persistence,
idempotent inventories, ping failure not suppressing SNMP, per-device failure isolation,
redaction, stale/decryption-failed credentials not suppressing TCP/Ping, backup default off,
missing backup credentials, concurrency limits, double-start protection, cancellation,
repeat scheduling without overlap, interrupted-run recovery, counter reset/wrap handling,
existing alert/incident/RCA integration, reports and formula-injection prevention,
manual-driver preservation, prefix boundaries, local ping errors, SSH command allowlist.

## UI checks

Three separate tabs, text import and auto-start, progress/results, history, report export,
page re-entry, navigation while a run is active, explicit stop and app close.
Inspected at 1400x900 and 980x600. Small windows use vertical scrolling.

## What has NOT been verified

No real user network was contacted. Device communication was simulated.
The build environment had no pysnmp/paramiko and could not reach the package repository;
real SNMPv2c/v3 transport/authentication, SSH host-key negotiation and device-specific CLI
must be validated on the user's machine after installing requirements.txt.
No real email or Telegram messages were sent. Native Windows UI was not tested here.
The application is source code, not a compiled EXE or an installed Windows Service.
Do not interpret passing offline tests as certification for every vendor/model/firmware.

## Reproduce offline tests

```text
python -m unittest discover -s tests -v
```

The new unit tests use temporary databases and mocked network adapters, not production devices.
For the existing regression_test.py, close the app and use a backup/copy of the project.
