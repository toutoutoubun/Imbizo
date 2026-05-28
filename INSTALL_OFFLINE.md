# Offline Installation

This guide explains how to install Imbizo-CS Workbench on a computer with no
internet connection.

## Recommended Release Package

A full release should provide:

- A Windows standalone build made with PyInstaller.
- A Linux standalone build made with PyInstaller.
- A Python wheel and source archive.
- A local wheelhouse containing pinned open-source Python wheels.
- `SHA256SUMS.txt` and `release_manifest_v<version>.json` for all release
  files.

The standalone build is the simplest option for researchers who do not use the
command line.

Maintainers prepare these artifacts with:

```bash
make release-check
make release-build
make wheelhouse
make offline-bundle
```

## Install From A Wheelhouse

On an internet-connected preparation machine:

```bash
python -m pip wheel .[gui,xlsx] --wheel-dir wheelhouse
```

Or create a transfer bundle:

```bash
python scripts/create_offline_bundle.py imbizo-offline-bundle
```

If you need the optional fastText LID model, download and audit it separately,
then pass `--fasttext-lid-file /path/to/lid.176.ftz`. The bundle script no
longer downloads model files directly; network access for bootstrap resources is
restricted to `tools/bootstrap.py` and `tools/make_bundle.py`.

Copy the repository archive and the `wheelhouse/` folder to the offline machine
with a USB drive or other local storage.

On the offline machine:

```bash
python -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse .
```

On Windows, use:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install --no-index --find-links wheelhouse .
```

If you transferred `lid.176.ftz`, set `IMBIZO_FASTTEXT_LID_MODEL` to the local
model path before launching. The app still works without this model by using the
documented local fallback.

## Verify Offline Operation

Run the test suite without network access:

```bash
PYTHONPATH=src pytest -q
```

Core workflows should work without internet:

- Create project.
- Import local files.
- Annotate.
- Run local LID suggestions.
- Compute metrics.
- Export local files.

## Optional Models And Plugins

Large optional resources such as AfroLID or local ASR models are not required
for the MVP. If a future plugin uses such resources, install them explicitly
from local files. The core app must continue working when optional plugins are
absent.

## v1.0 Offline Upgrade Addendum

Use this section when upgrading an existing MVP-era project to Imbizo-CS v1.0
on an air-gapped machine. Migration is local, additive, and opt-in. It adds
nullable noun-class, concord, and 4-M fields; it does not remove MVP data.

### 1. Create The v1.0 Transfer Bundle On A Connected Machine

From the Imbizo-CS v1.0 source tree:

```bash
python scripts/create_offline_bundle.py imbizo-v1_0-offline-bundle --include-fasttext-lid
```

The bundle contains:

- `wheelhouse/` with local Python wheels
- `dictionaries/` with v1.0 noun-class, concord, and 4-M YAML files
- `CHANGELOG.md` declaring dictionary versions
- `INSTALL_OFFLINE.md`
- `CITATION.cff`
- `SHA256SUMS.txt`

If you do not need the optional fastText model, omit
`--include-fasttext-lid`.

### 2. Verify Checksums Before Transfer

On Linux:

```bash
cd imbizo-v1_0-offline-bundle
sha256sum -c SHA256SUMS.txt
```

On Windows PowerShell:

```powershell
Get-Content .\SHA256SUMS.txt | ForEach-Object {
  $parts = $_ -split "\s+", 2
  $expected = $parts[0]
  $file = $parts[1]
  $actual = (Get-FileHash -Algorithm SHA256 $file).Hash.ToLower()
  if ($actual -ne $expected) { throw "Checksum mismatch: $file" }
}
```

Copy the entire bundle folder to a USB drive. After copying to the air-gapped
machine, run the same checksum command again from inside the copied bundle.

### 3. Install v1.0 From The Local Wheelhouse

Linux:

```bash
python -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse imbizo-cs-workbench
```

Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install --no-index --find-links wheelhouse imbizo-cs-workbench
```

### 4. Verify Dictionary Versions

Compare the transferred dictionary versions against `CHANGELOG.md`:

```bash
grep -R "^version:" dictionaries
grep -A6 "## 1.0.0" CHANGELOG.md
```

Each v1.0 starter dictionary should report `version: 0.1.0`. If a project-local
override is used, record that override in the project memo or provenance note.

### 5. Dry-Run The Migration

Before writing anything to the project:

```bash
imbizo-cs migrate --project /path/to/project --dry-run
```

Read the schema diff. It should list only additive token columns, new v1.0
tables, and indexes.

### 6. Run The Migration

```bash
imbizo-cs migrate --project /path/to/project
```

The command checks that the project is writable, checks free disk space, creates
a timestamped backup zip under the project’s `backups/` folder, applies the
v1.0 migration, writes provenance, and creates
`migration_report_v1_0.md` inside the project folder.

Avoid `--no-backup` unless you have already made your own verified copy:

```bash
imbizo-cs migrate --project /path/to/project --no-backup
```

### 7. First-Run No-Network Verification

Linux users can run a dry-run migration in a network namespace:

```bash
unshare --net --map-root-user imbizo-cs migrate --project /path/to/project --dry-run
```

If your Linux distribution does not allow `unshare`, disconnect networking
physically or through system settings, then run:

```bash
imbizo-cs migrate --project /path/to/project --dry-run
```

Windows users can open Resource Monitor, choose the Network tab, and watch the
`python.exe`, `imbizo.exe`, or `imbizo-cs.exe` process while opening the project
or running migration. There should be no TCP connections and no network send or
receive activity attributable to Imbizo-CS.

### 8. Restore If Needed

Restore to an empty folder:

```bash
imbizo-cs restore --from /path/to/project/backups/project.v1_0_pre_TIMESTAMP.zip --to /path/to/restored_project
```

Open the restored project or inspect its schema version. An MVP backup should
show the MVP schema version or lack v1.0 tables.

## v1.5 Offline Upgrade Addendum

Use this section when upgrading an existing v1.0 project to Imbizo-CS v1.5 on
an air-gapped machine. v1.5 adds sister-language disambiguation,
triggered-switching evidence, mixed-code variety mode, phonological integration
evidence, LIDES and CHAT/CLAN exporters, and offline community review. The
upgrade is additive: v1.0 noun-class, concord, and 4-M annotations are
preserved.

### 1. Prepare The v1.5 Bundle On A Connected Machine

```bash
mkdir -p imbizo-cs-v1.5-offline/wheels
python -m pip wheel ".[gui,xlsx,security,reports]" --wheel-dir imbizo-cs-v1.5-offline/wheels
cp -R dictionaries imbizo-cs-v1.5-offline/dictionaries
cp -R docs imbizo-cs-v1.5-offline/docs
cp README.md PRINCIPLES.md INSTALL_OFFLINE.md CITATION.cff CHANGELOG.md imbizo-cs-v1.5-offline/
find imbizo-cs-v1.5-offline -type f -print0 | sort -z | xargs -0 sha256sum > imbizo-cs-v1.5-offline/SHA256SUMS.txt
zip -r imbizo-cs-v1.5-offline.zip imbizo-cs-v1.5-offline
sha256sum imbizo-cs-v1.5-offline.zip > imbizo-cs-v1.5-offline.zip.sha256
```

Copy `imbizo-cs-v1.5-offline.zip` and
`imbizo-cs-v1.5-offline.zip.sha256` to the offline machine by USB or another
local transfer method.

### 2. Verify Checksums

Linux:

```bash
sha256sum -c imbizo-cs-v1.5-offline.zip.sha256
unzip imbizo-cs-v1.5-offline.zip
cd imbizo-cs-v1.5-offline
sha256sum -c SHA256SUMS.txt
```

Windows PowerShell:

```powershell
certutil -hashfile imbizo-cs-v1.5-offline.zip SHA256
```

Compare the printed hash with the value in the `.sha256` file. After
extraction, verify individual wheel and dictionary files against
`SHA256SUMS.txt` with an offline checksum tool.

### 3. Install v1.5 From The Local Wheelhouse

```bash
python -m pip install --no-index --find-links wheels imbizo-cs-workbench==1.5.0
```

The `--no-index` flag prevents contacting a package index. If any dependency is
missing from `wheels/`, the install should fail locally rather than reaching out
to the internet.

### 4. Install LIDES And CHAT/CLAN Exporters Offline

The v1.5 LIDES and CHAT/CLAN exporters are bundled Python modules. Confirm that
they import without remote validators:

```bash
python - <<'PY'
from imbizo.core.interop.lides import to_lides, validate_lides
from imbizo.core.interop.chat_clan import to_chat, validate_chat
print("LIDES exporter OK:", callable(to_lides), callable(validate_lides))
print("CHAT exporter OK:", callable(to_chat), callable(validate_chat))
PY
```

### 5. Verify No Outbound Network Call

Linux:

```bash
unshare -n imbizo-cs --help
unshare -n imbizo-cs migrate --project /path/to/project --target v1.5 --dry-run
```

Windows users can open Resource Monitor, choose the Network tab, and watch the
`python.exe`, `imbizo.exe`, or `imbizo-cs.exe` process while launching the app,
loading dictionaries, running migration dry-run, and rendering reports. There
should be no outbound connections.

### 6. Verify Dictionary Versions

```bash
imbizo-cs migrate --project /path/to/project --target v1.5 --dry-run
```

The dry-run lists discovered sister-language, trigger, mixed-code, and
phonology dictionary versions. Compare them with the release notes and any
project-local dictionary overrides.

### 7. Run The v1.5 Migration

```bash
imbizo-cs migrate --project /path/to/project --target v1.5
```

The command refuses MVP-era projects until v1.0 has been applied, creates a
pre-migration backup, applies only additive schema changes, writes provenance,
and creates `migration_report_v1_5.md` inside the project folder. Mixed-code
mode remains off until the researcher explicitly enables it after reading the
variety caveats.
