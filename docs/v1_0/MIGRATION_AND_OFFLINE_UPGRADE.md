# v1.0 Deliverable 9 — Migration And Offline Upgrade Path

This document describes the safe migration path from an MVP-era Imbizo-CS
project to v1.0. Migration is local, additive, and opt-in. It adds nullable
noun-class, concord, and 4-M storage while preserving MVP annotations.

## CLI Commands

The v1.0 CLI entrypoint is:

```bash
imbizo-cs migrate --project /path/to/project --dry-run
imbizo-cs migrate --project /path/to/project
imbizo-cs restore --from /path/to/backup.zip --to /path/to/empty_restore_folder
```

The implementation lives in `src/imbizo/cli.py` and uses Click. The migration
command:

- detects current schema version
- prints schema diff in dry-run mode without writes
- refuses read-only project folders
- refuses migration when free disk space is less than twice the project size
- creates a timestamped backup zip unless `--no-backup` is explicitly used
- applies the additive v1.0 migration
- writes provenance
- generates `migration_report_v1_0.md`

## GUI Migration Wizard

```text
+----------------------------------------------------------------------------+
| Welcome                                                                    |
| This wizard upgrades your local project to Imbizo-CS v1.0.                 |
| Links: docs/noun_classes.md | docs/four_m_model.md                         |
| [Cancel]                                                [Next]             |
+----------------------------------------------------------------------------+

+----------------------------------------------------------------------------+
| Backup confirmation                                                        |
| Backup will be written to: project/backups/project.v1_0_pre_TIMESTAMP.zip  |
| [Choose different location]                                                 |
| [Back] [Cancel]                                      [Create Backup]       |
+----------------------------------------------------------------------------+

+----------------------------------------------------------------------------+
| Schema diff preview                                                        |
| - Your project will gain a noun-class field on every token.                |
| - Your project will gain optional 4-M fields on every token.               |
| - New concord_links, noun_class_dictionaries, and four_m_audit tables.     |
| - Existing transcript and annotation data will not be modified.            |
| [Back] [Cancel]                                      [Apply Migration]     |
+----------------------------------------------------------------------------+

+----------------------------------------------------------------------------+
| Execute                                                                    |
| Progress: [########----------------]                                       |
| Append-only log:                                                           |
|  10:31 Checking SQLite database                                            |
|  10:31 Creating backup                                                     |
|  10:32 Applying schema changes                                             |
|  10:32 Writing provenance                                                  |
+----------------------------------------------------------------------------+

+----------------------------------------------------------------------------+
| Verification                                                               |
| [x] Backup exists                                                          |
| [x] Schema version is now v1.0                                             |
| [x] Dictionaries loaded                                                    |
| [x] Provenance event written                                               |
| [x] migration_report_v1_0.md created                                       |
| [Back]                                                   [Done]            |
+----------------------------------------------------------------------------+

+----------------------------------------------------------------------------+
| Done                                                                       |
| [Open this project now]  [Restore from backup if needed]                   |
+----------------------------------------------------------------------------+
```

### Wizard Flow

1. Welcome: explain that the migration is additive and links to
   `docs/noun_classes.md` and `docs/four_m_model.md`.
2. Backup confirmation: show the default backup zip path and allow a different
   user-chosen location.
3. Schema diff preview: use plain language, not SQL, and state that existing
   data will not be modified.
4. Execute: show progress and an append-only log pane.
5. Verification: show backup, schema, dictionary, provenance, and report
   checklist.
6. Done: offer "Open this project now" and "Restore from backup if needed."

## Rollback Procedure

Locate the pre-migration backup zip:

```bash
ls /path/to/project/backups/*v1_0_pre*.zip
```

Restore to an empty folder:

```bash
imbizo-cs restore --from /path/to/project/backups/project.v1_0_pre_TIMESTAMP.zip --to /path/to/restored_project
```

Verify that the restored project is MVP-era:

```bash
imbizo-cs migrate --project /path/to/restored_project --dry-run
```

The dry-run should again show the v1.0 schema additions as pending. You can
also inspect the restored database hash against the migration report's
pre-migration SHA-256.

To record an offline bug report for later submission, create or append:

```bash
mkdir -p /path/to/restored_project/logs
printf "## Migration issue\n\n- Date:\n- Imbizo-CS version:\n- What happened:\n" >> /path/to/restored_project/logs/local_issues.md
```

Do not upload interview data when later submitting the issue. Share the error
message, migration report, and schema diff instead.

## Post-Migration Verification Report

After successful migration, the CLI writes `migration_report_v1_0.md` inside
the project folder.

```markdown
# Imbizo-CS v1.0 Migration Report

Timestamp: 2026-05-27T00:00:00Z

Imbizo-CS version: MVP-era project -> 1.0.0

Schema version: 1 -> 1.0.0

Backup zip: project/backups/project.v1_0_pre_TIMESTAMP.zip

SQLite pre-migration backup: project/backups/project.sqlite.v1_0_pre_TIMESTAMP.bak

## Schema Diff Summary

- ALTER TABLE tokens ADD COLUMN nc_class INTEGER NULL
- ALTER TABLE tokens ADD COLUMN nc_prefix TEXT NULL
- ALTER TABLE tokens ADD COLUMN nc_source TEXT NULL
- ALTER TABLE tokens ADD COLUMN four_m_type TEXT NULL
- ALTER TABLE tokens ADD COLUMN four_m_source TEXT NULL
- CREATE TABLE IF NOT EXISTS noun_class_dictionaries
- CREATE TABLE IF NOT EXISTS concord_links
- CREATE TABLE IF NOT EXISTS four_m_audit

## Dictionary Versions Loaded

- dictionaries/noun_classes/zul.yaml: version 0.1.0
- dictionaries/concord/zul.yaml: version 0.1.0
- dictionaries/four_m/eng.yaml: version 0.1.0

## Provenance

Provenance event id: UUID

## Database Hashes

- Pre-migration project.sqlite SHA-256: HASH
- Post-migration project.sqlite SHA-256: HASH

## Reproducibility Statement

To reproduce this migration, restore the backup zip, install Imbizo-CS v1.0
from the same offline bundle, and run imbizo-cs migrate --project <project>.
No telemetry, network service, or external API is required.
```

## Test Plan

The following pytest cases must pass before v1.0 ships:

1. Migrate an MVP project with zero annotations: succeeds, schema upgraded,
   existing data unchanged.
2. Migrate an MVP project with approximately 500 annotations: succeeds, all
   existing rows preserved, new columns remain NULL until reviewed.
3. Migrate a corrupted project with a truncated SQLite file: fails gracefully
   with a clear error and does not apply migration changes.
4. Restore from backup: restored `project.sqlite` SHA-256 matches the
   pre-migration hash recorded in `migration_report_v1_0.md`.
5. Run migrate twice: the second run is a no-op for already-added columns and
   leaves the project usable.

