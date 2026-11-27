# Level_10_Meeting

## Rules report

```bash
tools/report.sh > rules_report.json
APP_NOW=2026-11-18T15:00:00Z tools/report.sh
```

- Prints every value from brief 2.6 as JSON, in the format in `assessment/README.md`.
- Each run builds its own database (`<db>_report`): migrate, seed, compute, drop. Your dev data is untouched. Needs Postgres running and a role that can create databases.
- JSON goes to stdout, logs to stderr.

**Assumptions**
- Every seeded Rock is included, not only the current quarter's.
- Another `APP_NOW` moves only the clock; the data stays as seeded.
