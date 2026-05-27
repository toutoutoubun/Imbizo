# Offline Installation

This guide explains how to install Imbizo-CS Workbench on a computer with no
internet connection.

## Recommended Release Package

A full release should provide:

- A Windows standalone build made with PyInstaller.
- A Linux standalone build made with PyInstaller.
- A source archive.
- A local wheelhouse containing pinned open-source Python wheels.
- Checksums for all release files.

The standalone build is the simplest option for researchers who do not use the
command line.

## Install From A Wheelhouse

On an internet-connected preparation machine:

```bash
python -m pip wheel .[gui,xlsx] --wheel-dir wheelhouse
```

Or create a transfer bundle:

```bash
python scripts/create_offline_bundle.py imbizo-offline-bundle --include-fasttext-lid
```

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
