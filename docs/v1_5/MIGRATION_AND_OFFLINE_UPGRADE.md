# v1.5 Deliverable 9 - Migration and Offline Upgrade Path

This deliverable defines the safe local upgrade path from Imbizo-CS v1.0 to
v1.5. It covers offline installation, CLI migration, GUI migration flow,
rollback, post-migration verification, and release test cases. The migration is
additive: v1.0 noun-class, concord, and 4-M data are preserved, and all v1.5
features remain opt-in.

## 1. INSTALL_OFFLINE.md v1.5 Addendum

The v1.5 addendum is implemented in `INSTALL_OFFLINE.md`. It includes:

- Preparing a v1.5 offline bundle on a connected machine.
- Bundling wheels, dictionaries, docs, and checksums.
- Transferring the zip by USB.
- Verifying the zip and every artifact with SHA-256.
- Installing wheels with `--no-index`.
- Confirming that LIDES and CHAT/CLAN exporters import offline.
- Verifying first launch with no outbound network calls.

Example checksum commands:

```bash
sha256sum -c imbizo-cs-v1.5-offline.zip.sha256
unzip imbizo-cs-v1.5-offline.zip
cd imbizo-cs-v1.5-offline
sha256sum -c SHA256SUMS.txt
```

The LIDES and CHAT/CLAN exporters are local modules and must not contact remote
validators:

```bash
python - <<'PY'
from core.interop.lides import to_lides, validate_lides
from core.interop.chat_clan import to_chat, validate_chat
print(callable(to_lides), callable(validate_lides))
print(callable(to_chat), callable(validate_chat))
PY
```

## 2. CLI Command - `imbizo-cs migrate`

The extended command is implemented in `cli.py`. The public command signature is:

```python
@click.command()
@click.option("--project", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--target", type=click.Choice(["v1.0", "v1.5"]), default="v1.5")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--no-backup", is_flag=True, default=False)
def migrate(project: Path, target: str, dry_run: bool, no_backup: bool) -> None:
    """Upgrade a project to the requested Imbizo-CS schema version."""
```

Behavior:

- Detects the current schema from the project SQLite database.
- Refuses MVP -> v1.5 skipping with a clear message directing the user to v1.0.
- Treats re-running on a v1.5 project as a no-op.
- In `--dry-run`, prints the schema diff without writes.
- In normal mode, verifies the project is writable.
- Refuses migration when free disk space is less than 2x project size.
- Creates a pre-migration backup unless `--no-backup` is set.
- If `--no-backup` is set, requires typed confirmation: `NO BACKUP`.
- Applies the v1.5 additive migration.
- Writes provenance and `migration_report_v1_5.md`.

Example:

```bash
imbizo-cs migrate --project /path/to/project --target v1.5 --dry-run
imbizo-cs migrate --project /path/to/project --target v1.5
```

## 3. GUI Migration Wizard - v1.5 Path

```text
+------------------------------------------------------------------------------+
| Imbizo-CS Migration Wizard: v1.0 -> v1.5                                      |
+------------------------------------------------------------------------------+
| Step 1 Welcome                                                                |
| v1.5 adds sister-language disambiguation, triggers, mixed-code mode,          |
| phonological integration, LIDES/CHAT exports, and community review.           |
| Links: sister_languages.md | triggers.md | mixed_codes.md |                   |
| phonological_integration.md | interop_lides_chat.md | community_review.md     |
| [Cancel] [Next]                                                               |
+------------------------------------------------------------------------------+
| Step 2 Pre-flight check                                                       |
| [OK] Project folder writable                                                  |
| [OK] SQLite database found                                                    |
| [OK] Current schema is v1.0                                                    |
| [FAIL] MVP schema detected: apply v1.0 first                                  |
| [Back] [Next]                                                                 |
+------------------------------------------------------------------------------+
| Step 3 Backup confirmation                                                    |
| Backup destination: /project/backups/pre_v1_5_YYYYMMDDTHHMMSSZ.zip            |
| [Choose different location]                                                   |
| [x] I understand this backup is needed to roll back safely                    |
| [Back] [Next]                                                                 |
+------------------------------------------------------------------------------+
| Step 4 Schema diff preview                                                    |
| Your project will gain nullable token fields for sister-language evidence,    |
| trigger role, mixed-code variety, and phonological integration score.          |
| New tables: trigger_links, mixed_code_spans, phonological_features,            |
| community_reviews. Existing v1.0 data will not be modified.                   |
| [Back] [Next]                                                                 |
+------------------------------------------------------------------------------+
| Step 5 Dictionary opt-in selection                                            |
| [ ] Sister-language disambiguation                                            |
| [ ] Trigger detection                                                         |
| [ ] Mixed-code mode (off by default)                                          |
|     If enabled: select varieties and read caveats before continuing.          |
| [ ] Phonological integration                                                  |
| [x] Interop exports (always on)                                                |
| [ ] Community review                                                          |
| [Back] [Next]                                                                 |
+------------------------------------------------------------------------------+
| Step 6 Execute                                                                |
| Progress: [########################----------------]                           |
| Append-only log: backup created, schema diff applied, provenance written      |
| [Back disabled] [Cancel disabled after DB transaction begins]                  |
+------------------------------------------------------------------------------+
| Step 7 Verification                                                           |
| [OK] Backup exists                                                            |
| [OK] Schema version is v1.5                                                    |
| [OK] Dictionaries loaded                                                       |
| [OK] Provenance event written                                                  |
| [OK] migration_report_v1_5.md created                                          |
| [Back] [Next]                                                                 |
+------------------------------------------------------------------------------+
| Step 8 Done                                                                   |
| [Open this project] [Restore from backup] [Close]                             |
+------------------------------------------------------------------------------+
```

The wizard never enables mixed-code mode silently. If a researcher checks
"Mixed-code mode", the wizard pauses and displays the caveats text for each
selected variety before allowing "Next".

## 4. Rollback Procedure

Rollback uses the pre-migration backup zip created before any v1.5 writes.
Restoring this zip returns the project to the exact v1.0 state that existed
before migration, including all v1.0 annotations created before migration.

```bash
imbizo-cs restore --from /path/to/pre_v1_5_backup.zip --to /path/to/project
```

The restore command:

- Computes the SHA-256 hash of the SQLite database inside the backup zip.
- Restores the zip into the requested project directory.
- Computes the SHA-256 hash of the restored database.
- Fails verification if the two hashes differ.

If the target directory is not empty, the command requires typed confirmation:

```text
RESTORE
```

Do not restore into a new path and then manually copy files over an existing
project. Use the restore command so the hash verification remains meaningful.

## 5. Post-Migration Verification Report

After a successful migration, Imbizo-CS writes
`migration_report_v1_5.md` inside the project folder.

```markdown
# Imbizo-CS v1.5 Migration Report

Generated at: `2026-05-27T00:00:00+00:00`

## Version transition

- From schema: `1.0`
- To schema: `1.5`
- Imbizo-CS transition: `v1.0 -> v1.5`

## Schema diff summary

Added nullable token columns:

- `tokens.sister_lang_confidence`
- `tokens.sister_lang_evidence`
- `tokens.trigger_role`
- `tokens.mixed_code_variety`
- `tokens.phon_integration_score`

Created tables:

- `trigger_links`
- `mixed_code_spans`
- `phonological_features`
- `community_reviews`

## Dictionary versions loaded

- `sister_lang.zul_vs_xho`: `0.1.0`
- `triggers.eng`: `0.1.0`
- `mixed_code.tsotsitaal`: `0.1.0`
- `phonology.zul`: `0.1.0`

## v1.5 feature opt-ins

- `sister_language_disambiguation`: `false`
- `trigger_detection`: `false`
- `mixed_code_mode`: `false`
- `phonological_integration`: `false`
- `interop_exports`: `true`
- `community_review`: `false`

## Provenance

- Provenance event id: `<uuid>`
- Backup path: `<backup.zip>`

## Database hashes

- Pre-migration SQLite SHA-256: `<hash>`
- Post-migration SQLite SHA-256: `<hash>`

## Reproducibility statement

Restore the pre-migration backup zip, open the project with Imbizo-CS v1.5,
confirm the dictionary versions, and rerun
`imbizo-cs migrate --project <project_dir> --target v1.5`.
```

## 6. Test Plan

The following pytest cases must pass before v1.5 ships:

- Migrate a v1.0 project with zero v1.0-specific annotations: schema upgraded,
  existing data unchanged.
- Migrate a v1.0 project with `concord_links` and `four_m_audit` data: all
  existing rows preserved, new token columns NULL.
- Migrate an MVP project: refused with a clear message directing the user to
  apply v1.0 first.
- Migrate twice: second run is a no-op.
- Restore from backup: exact SHA-256 match between the backed-up database and
  restored database.
- Migrate with `--dry-run`: no writes, full diff printed.
- Migrate with mixed-code mode disabled: no mixed-code rows are populated;
  opting in later works without re-migration.

These cases should run without internet access and without contacting external
validators for LIDES, CHAT/CLAN, or dictionary files.
