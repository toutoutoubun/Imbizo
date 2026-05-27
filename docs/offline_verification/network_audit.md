# Network Audit

Core workflows must not perform network calls:

- Launch application.
- Create/open project.
- Import local files.
- Annotate.
- Run bundled/local LID suggestions.
- Compute metrics.
- Export local files.

The MVP codebase contains no cloud SDKs, telemetry clients, account flows, or
mandatory model downloads.
