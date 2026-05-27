# Imbizo-CS Workbench

Imbizo-CS Workbench is a local research workbench for people studying
code-switching in South African multilingual interview data.

It is designed for humanities and social-science researchers who need to keep
their material on their own computer. The app works with local project folders:
your transcripts, annotations, logs, dictionaries, and exports stay inside the
folder you choose.

Imbizo-CS Workbench is not a cloud assistant. It does not require an account,
subscription, API key, telemetry, or internet connection for core work.

## What You Can Do In The MVP

- Create and open a local research project.
- Import TXT, CSV, TSV, JSON, XLSX, ODS, ELAN EAF, Praat TextGrid, audio, and
  video files.
- Continue annotating imported transcript data at token level.
- Keep original transcript text separate from optional normalized text.
- Add or override language labels manually.
- Record Matrix Language, Embedded Language, switch type, linguistic status,
  trigger text, confidence, tags, memos, and morpheme splits.
- Run local language-identification suggestions that remain editable.
- Compute language proportions, switch count, switch density, dominant language,
  M-index, I-index, burstiness, trigger tables, and KWIC concordance.
- Export CSV, XLSX, JSON, EAF, TextGrid, HTML, PDF, and quotation extracts.

## Supported Languages

Default project language labels include:

- English
- Afrikaans
- isiZulu
- isiXhosa
- Sesotho
- Setswana
- unknown
- mixed
- borrowing
- proper noun

You can add your own language or variety labels, such as Tsotsitaal, Iscamtho,
Kaaps, or Sabela.

## How Projects Are Stored

Each project is a normal folder. Inside it, Imbizo creates:

- `project.sqlite` for structured project data.
- `media/` for copied audio and video.
- `transcripts/` for copied transcript sources.
- `dictionaries/` for editable local dictionaries.
- `logs/provenance.jsonl` for readable provenance records.
- `exports/` for local export files.
- `cache/` for rebuildable waveform and analysis caches.

Imported source files are copied into the project folder. The original source
file is not modified.

## Your First Project

This walkthrough uses a fictional isiZulu-English interview.

1. Choose a local folder such as `Documents/ImbizoProjects/DurbanInterview`.
2. Create a project and fill in title, researcher, institution, location, date,
   ethics notes, consent status, and IRB/REC reference if you have one.
3. Import a transcript file. For example:

   ```text
   I went ekhaya yesterday.
   Ngiyabonga for helping me.
   The class ibinzima today.
   ```

4. Open the annotation editor.
5. Select each token and set its language label. You can use English, isiZulu,
   unknown, mixed, borrowing, proper noun, or your own project labels.
6. Add Matrix Language and Embedded Language where useful. The app supports
   this framework but does not force it.
7. Add qualitative memos for topic shifts, classroom register, identity work,
   religious register, repair, or uncertainty.
8. Run local LID suggestions if you want assistance. Suggestions marked `auto`
   are never final.
9. Compute M-index, I-index, and burstiness from your current annotations.
10. Export CSV/XLSX for checking, JSON for archiving, and HTML/PDF for reading.

## Glossary

Matrix Language:

The language that provides the main grammatical frame in Matrix Language Frame
analysis (Myers-Scotton, 1993).

Embedded Language:

The language inserted into the Matrix Language frame (Myers-Scotton, 2002).

M-index:

A measure of how evenly languages are distributed in annotated data. Higher
values usually mean a more balanced multilingual distribution (Barnett et al.,
2000).

I-index:

A measure of how often adjacent annotated token boundaries are switch points
(Guzman et al., 2017).

Burstiness:

A measure of whether switches cluster together or appear more evenly across the
interview (Goh & Barabasi, 2008).

Trigger word or phrase:

A word or phrase that may help explain a switch, following trigger-based coding
in language-contact analysis (Clyne, 2003).

## Running From Source

For command-line workflows and tests:

```bash
PYTHONPATH=src pytest -q
```

To launch the desktop GUI, install the optional GUI dependency in your local
environment:

```bash
python -m pip install -e ".[gui,xlsx,dev]"
imbizo
```

The GUI requires PySide6. The non-GUI core can still create projects, import
files, annotate, compute metrics, and export through Python services.

## How To Cite Imbizo-CS

Use the included [CITATION.cff](CITATION.cff). A plain-text citation can begin:

```text
Imbizo-CS Workbench Contributors. (2026). Imbizo-CS Workbench
(Version 0.1.0) [Computer software]. DOI placeholder:
10.0000/imbizo-cs-workbench.placeholder
```

Every export also writes a neighboring `.CITATION.cff` sidecar so exported
tables and reports keep their software-citation context.

## Design Promise

Automatic analysis is only assistance. The researcher remains the final
authority. Every automatic label is stored as automatic, provenance is recorded,
and manual annotation takes precedence.
