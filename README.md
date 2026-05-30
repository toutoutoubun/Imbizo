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

### Optional Coarse Language Group Gate

Local LID suggestions can now be run with an optional coarse language group
gate. This is not a final language classifier. It groups candidate evidence
into broad South African language families such as Germanic, Nguni, and
Sotho-Tswana, then blocks only risky auto-annotation when the evidence is too
weak or when closely related languages are hard to separate. Suggestions are
still saved in `lid_suggestions.evidence_json` for audit and review.

The gate is off by default, never overwrites manual or imported annotations,
and does not change Matrix Language, Embedded Language, switch-type, tags,
memos, morpheme splits, or existing export columns. Ambiguity is a valid
scholarly result: use speaker knowledge, context, grammars, and community
review when exact labels matter.

In the desktop Annotation tab, enable the `Coarse group gate` checkbox before
clicking `Run Local LID` to use this conservative filter for that run. The
Metrics tab also includes a `LID Accuracy` view. It compares active automatic
labels with manual/imported review labels per language, so a row such as
`zul: 73%` means "73% of reviewed isiZulu tokens currently have a matching
auto label." If no manual/imported labels exist, Imbizo-CS does not claim an
accuracy value.

## What's New In v1.0

Version 1.0 adds three optional layers for researchers who need to study how
borrowed or inserted material is integrated into Bantu-language grammatical
frames. These tools are not automatic interpretation. They are local,
reviewable annotation aids that keep the researcher in control.

Noun class:

- You can record a noun-class number, matched prefix, and source for a token.
- The Noun Class panel reads local YAML dictionaries for isiZulu, isiXhosa,
  Sesotho, and Setswana and suggests possible classes by string matching.
- Shipped dictionary entries that need review are marked `verified: false`,
  so you can see uncertainty instead of inheriting it silently.
- Project-local dictionary overrides live inside your project folder and travel
  with project exports.

Concord:

- You can ask Imbizo-CS to show concord candidates for a selected class-tagged
  head noun.
- Candidate concord tokens are found through pure dictionary prefix matching,
  not machine learning.
- Confirmed, uncertain, or rejected links are stored in the local SQLite
  database and logged in provenance.
- Concord evidence can feed a transparent integration score, whose weights are
  visible and editable for sensitivity analysis.

4-M and MLF audit:

- The annotation grid can store optional 4-M tags: `content`,
  `early_system`, `bridge_late_system`, and `outsider_late_system`.
- The MLF audit report summarizes whether reviewed system morphemes appear
  consistent with a single Matrix Language, mixed, or insufficiently annotated.
- The verdict is advisory. It never overwrites your Matrix Language, Embedded
  Language, switch-type, or memo annotations.

Here is a short fictional walkthrough:

```text
Ngithenge i-laptop entsha izolo.
# fictional or paraphrased; verify with a reference grammar for publication
```

First, annotate the token languages as you normally would. You might label the
stem in `i-laptop` as English-origin while treating the surrounding utterance
as isiZulu. Next, open the Noun Class panel and review suggestions for
`i-laptop`. If class 9 is appropriate for your analysis, accept it or override
it with your own note. Then click "Show concord candidates" to inspect whether
`entsha` should be recorded as a concord relation. If you confirm the link, the
project stores that decision with dictionary version and provenance. Finally,
use the 4-M dropdown to tag reviewed morphemes. The MLF audit report will then
show whether your reviewed system-morpheme evidence looks consistent, mixed, or
still under-annotated.

Read more in [docs/noun_classes.md](docs/noun_classes.md) and
[docs/four_m_model.md](docs/four_m_model.md). Those guides are written for
humanities researchers rather than software developers. They explain how to
read warnings, when to leave a field blank, and how to cite the relevant
linguistic framework in a methods chapter.

### v1.0 Limitations

The dictionaries are starter resources, not grammar authorities. Many entries
are intentionally marked `verified: false` and should be checked against a
reference grammar, speaker knowledge, or community review before publication.

The sister-language disambiguation problem is deferred to v1.5. Imbizo-CS v1.0
does not try to decide whether an ambiguous form belongs to isiZulu or isiXhosa,
or to Sesotho or Setswana. It uses the language label and dictionary you choose.

The app still does not bundle full morphological analyzers. It supports manual
morpheme splitting, dictionary hints, and reviewed concord links, but it does
not parse Bantu morphology automatically.

Bundled ASR is also still out of scope. Manual transcription remains the
default, and future ASR support must stay local, optional, and reviewable.

## What's New in v1.5

v1.5 adds six opt-in feature blocks. Existing MVP and v1.0 projects remain
compatible, and all new fields are additive.

**C1 - Sister Language Disambiguator.** v1.5 adds local, rule-based support for
cases where lightweight language identification cannot confidently separate
closely related languages, such as isiZulu and isiXhosa or Sesotho and
Setswana. The disambiguator reads project dictionaries, reports evidence tags,
and gives a ranked suggestion. It does not decide the language for you. See
[docs/sister_languages.md](docs/sister_languages.md).

**C2 - Triggered Switching Detector.** v1.5 adds a Clyne-style trigger lens for
proper nouns, borrowings, cognates, discourse markers, and other words that may
appear near switch boundaries (Clyne, 1967, 2003). Trigger candidates must be
confirmed or rejected by the researcher. See [docs/triggers.md](docs/triggers.md).

**C3 - Mixed-Code Variety Mode.** v1.5 makes room for Tsotsitaal, Iscamtho,
Kaaps, Sabela, and project-local mixed-code labels without forcing them into a
simple two-language switch model. This mode is off by default and includes
strong caveats. See [docs/mixed_codes.md](docs/mixed_codes.md).

**D1 - Borrowing Integration Score v2.** v1.5 extends the v1.0 integration
score with optional phonological evidence such as vowel epenthesis, cluster
simplification, and tonal reassignment. Projects without audio can leave these
fields blank. See
[docs/phonological_integration.md](docs/phonological_integration.md).

**D2 - LIDES and CHAT/CLAN Export.** v1.5 adds export paths for international
code-switching and transcript-analysis workflows while documenting losses in
sidecar validation reports. See
[docs/interop_lides_chat.md](docs/interop_lides_chat.md).

**D3 - Community Review Workflow.** v1.5 adds offline review packets for
dictionaries and sensitive annotations. Packets can be moved by USB, checked
with a local signature hash, and queued for manual acceptance. See
[docs/community_review.md](docs/community_review.md).

### v1.5 Walkthrough

Imagine an isiZulu-English interview used in earlier project examples. One
utterance contains `Ngithenge i-laptop entsha izolo` (# fictional example). In
v1.0, you could mark `i-laptop` as a class 9 integrated English stem and confirm
agreement with `entsha`. In v1.5, you can add phonological evidence if the audio
supports it, such as an audible vowel adaptation, then compare the v1.0 and v2
integration scores.

Later, the participant mentions a `manager` and then continues in English
(# fictional example). The Triggered Switching Detector may flag `manager` as a
candidate trigger because it appears just before the switch boundary. You can
confirm it, reject it, or write a memo saying the switch is better explained by
reported speech or institutional register.

In another utterance, a short token is tied between isiZulu and isiXhosa
(# fictional example). The Sister Language Disambiguator opens an evidence
panel with dictionary cues and a confidence score. If the evidence is weak,
leave the token ambiguous. Ambiguity is a valid scholarly result.

Finally, suppose a speaker uses vocabulary that resembles a project-local
Tsotsitaal profile (# fictional example). Mixed-code mode can suggest a span,
but it will display a warning that lexical evidence is not the same as
identifying a speaker, variety, or text. You decide whether the label fits your
project's ethics, context, and theory.

### v1.5 Limitations

Sister-language disambiguation is heuristic, not authoritative. Trigger
detection is suggestive only. Mixed-code mode is a starting point for variety
analysis, not a definition of Tsotsitaal, Iscamtho, Kaaps, Sabela, or any living
practice. LIDES and CHAT/CLAN exports have documented losses. Community review
depends on people having time, trust, and authority to comment; the workflow
supports review, but it does not manufacture community consent.

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

## Installing A Release Package

Imbizo-CS Workbench can be installed as a local Python package from the release
wheel:

```bash
python -m pip install imbizo_cs_workbench-1.5.0-py3-none-any.whl
imbizo-cs --help
```

For an air-gapped machine, use the offline bundle and install with `--no-index`
so pip cannot contact a package index:

```bash
python -m pip install --no-index --find-links wheelhouse imbizo-cs-workbench
```

Maintainers preparing a release should run:

```bash
make release-check
make release-build
```

The build writes wheel, source distribution, `SHA256SUMS.txt`, and a JSON
release manifest into `dist/`. Full maintainer instructions are in
[docs/release_packaging.md](docs/release_packaging.md).

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
(Version 1.5.0) [Computer software]. DOI placeholder:
10.0000/imbizo-cs-workbench.placeholder
```

Every export also writes a neighboring `.CITATION.cff` sidecar so exported
tables and reports keep their software-citation context.

## Design Promise

Automatic analysis is only assistance. The researcher remains the final
authority. Every automatic label is stored as automatic, provenance is recorded,
and manual annotation takes precedence.

## Bootstrap Resource Licence Summary

Imbizo-CS source code is AGPLv3, but imported resources keep their own licences.
The bootstrap subsystem therefore installs Core resources by default and gates
Optional-NC or Community resources behind explicit acknowledgement.

| Resource | Licence | Tier | AGPLv3 combinable? | Commercial use? | ShareAlike? | Default install? |
| --- | --- | --- | --- | --- | --- | --- |
| UP Multilingual Lexicons | CC-BY-4.0 | 1 | combination | yes | no | yes |
| Mafoko / za-mavito | NOODL or CC-BY-NC-SA-2.5-ZA | 3 | aggregation only | restricted where NC rows apply | yes where SA rows apply | no |
| African Wordnet verified subset | CC-BY-4.0 | 1 | combination | yes | no | yes |
| UNISA Termbank | Per-file SADiLaR metadata; converted files resolve to CC-BY-4.0 or OER-UNISA when verified | 1 for converted files only | combination after per-file verification | yes for converted Tier-1 files | no for converted Tier-1 files | yes, but unknown / NC files are skipped |
| EXDN | Public Domain | 1 | combination | yes | no | yes |
| fastText lid.176 compressed | CC-BY-SA-3.0 | 2 | aggregation only | yes | yes | no |
| fastText lid.176 full | CC-BY-SA-3.0 | 2 | aggregation only | yes | yes | no |
| NCHLT Text Corpora | CC-BY-2.5-SA | 1 | aggregation only | yes | no | yes |
| Morphologically Annotated Corpora | CC-BY-4.0 when verified | 1 | combination | yes | no | yes |
| MasakhaPOS | CC-BY-NC-4.0 | 2 | aggregation only | no | no | no |
| MasakhaNER | CC-BY-NC-4.0 | 2 | aggregation only | no | no | no |
| ZA_LEX | Apache-2.0 / MIT plus per-language files | 1 | combination | yes | no | yes |
| whisper.cpp source | MIT | 1 | combination | yes | no | no, ASR opt-in |
