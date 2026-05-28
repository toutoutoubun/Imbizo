# Release Packaging

This guide is for maintainers preparing an Imbizo-CS Workbench release as a
software package. It keeps the project aligned with the offline-first and data
sovereignty commitments in `PRINCIPLES.md`: release tooling may build local
artifacts, but it does not upload to PyPI, call telemetry services, or fetch
runtime resources behind the researcher's back.

## Release Artifacts

For each release, publish these files together:

- `imbizo_cs_workbench-<version>-py3-none-any.whl`
- `imbizo_cs_workbench-<version>.tar.gz`
- `SHA256SUMS.txt`
- `release_manifest_v<version>.json`
- `INSTALL_OFFLINE.md`
- the optional offline wheelhouse or USB bundle, when prepared for an
  air-gapped site

The wheel is the normal Python package. The source distribution preserves the
documentation, dictionaries, bootstrap manifest, tests, and release scripts for
auditability. Large processing resources and imported dictionaries remain
outside the core wheel and are installed through the bootstrap/offline-bundle
workflow.

## Pre-release Checklist

Run the release check from a clean checkout:

```bash
make release-check
```

This verifies version metadata, citation metadata, entry-point imports, runtime
offline guards, licence-compliance metadata, and the full offline pytest suite.
If a dependency is missing, install it from a local wheelhouse or from the
connected maintainer machine before preparing the final release.

The release check must pass before tagging. If it fails because optional GUI or
report dependencies are absent, either install the corresponding optional group
from the audited wheelhouse or record the missing optional dependency in the
release notes.

## Build The Package

Build the source distribution and wheel locally:

```bash
make release-build
```

The command writes artifacts to `dist/` and creates both `SHA256SUMS.txt` and a
JSON release manifest. The script uses the setuptools backend declared in
`pyproject.toml`, so it can run without the external `build` package. If you
prefer the standard PyPA frontend, install the `release` optional dependency
group and run `python -m build`.

Inspect the generated checksums:

```bash
cat dist/SHA256SUMS.txt
python -m json.tool dist/release_manifest_v1.5.0.json
```

Attach these files to the GitHub release or copy them into the offline release
bundle. Do not edit artifacts after checksums are written.

## Build An Offline Bundle

On a connected maintainer machine, create a wheelhouse:

```bash
make wheelhouse
```

Then create the USB-transfer bundle:

```bash
make offline-bundle
```

The bundle contains local wheels, documentation, dictionaries, and checksums.
Optional external resources such as fastText, MasakhaPOS, MasakhaNER, or ASR
models remain gated by the bootstrap tiering system and must not be silently
added to the default bundle.

## Verify Installation Offline

On the offline machine, install with `--no-index`:

```bash
python -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse imbizo-cs-workbench
.venv/bin/python scripts/verify_offline_install.py
```

Windows users should use `.venv\Scripts\python` for the same commands. The
important property is `--no-index`: if a wheel is missing, installation fails
locally instead of contacting a package index.

## Tagging And Publication

Only tag after the release check and artifact build pass:

```bash
git tag -a v1.5.0 -m "Imbizo-CS Workbench v1.5.0"
git push origin v1.5.0
```

Publishing to PyPI is not the default distribution path because many Imbizo-CS
installations are air-gapped. If a PyPI upload is later approved by project
governance, it must be treated as a mirror of the signed GitHub artifacts, not
as the source of truth.
