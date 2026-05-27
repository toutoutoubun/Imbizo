# Deliverable 1 — Architecture Overview

Imbizo-CS Workbench is a local desktop workbench for humanities researchers
studying code-switching in South African multilingual data. The system follows
a layered architecture: PySide6 GUI, application services, domain models,
SQLite repositories, local processing engines, and optional plug-in boundaries.
This follows the interaction style of established local humanities tools such
as ELAN and Praat while adding project-level provenance and code-switching
annotation support (Wittenburg et al., 2006; Boersma & Weenink, 2024).

```text
Researcher
  |
  v
PySide6 GUI
  |-- annotation editor
  |-- spreadsheet view
  |-- timeline view
  |-- metrics dashboard
  |-- project settings
  v
Application services
  |-- project/import/annotation/LID/morphology/metrics/export/provenance/security
  v
Domain model
  |-- projects, languages, transcripts, tokens, annotations, metrics, provenance
  v
Persistence and local files
  |-- project.sqlite
  |-- media/
  |-- transcripts/
  |-- dictionaries/
  |-- exports/
  |-- logs/provenance.jsonl
  |-- cache/
```

Architectural justifications:

- Offline-first: SQLite and plain files avoid cloud infrastructure.
- Data sovereignty: the project folder is the custody boundary.
- Low-resource operation: CPU-only processing, small local resources, lazy
  media loading, and optional large models.
- Humanities-led analysis: automatic labels are stored as suggestions and
  manual annotations are authoritative.
- Reproducibility: imports, automatic decisions, manual edits, metrics, and
  exports are logged with provenance, aligning with FAIR4RS and FORCE11
  software-citation principles (Chue Hong et al., 2022; Smith et al., 2016).
- Interoperability: EAF and TextGrid support preserve links to ELAN and Praat
  workflows; tabular import/export supports Excel and LibreOffice Calc.
- Decolonial posture: defaults do not assume English-only workflows, cloud
  access, or global-North infrastructure (Ali, 2016; Risam, 2018).

Academic precedents informing the architecture include ELAN for multimodal
annotation, Praat for phonetic time-aligned data, FLEx for language-documentation
workflows, SADiLaR resources for South African languages, and code-switching
corpora that show the need to handle three-language utterances rather than drop
them (Wittenburg et al., 2006; Boersma & Weenink, 2024; Eiselen &
Puttkammer, 2014; Van der Westhuizen & Niesler, 2018).

# Deliverable 2 — Directory Layout

The repository is a single Python monorepo:

```text
Imbizo/
|-- PRINCIPLES.md
|-- README.md
|-- INSTALL_OFFLINE.md
|-- CITATION.cff
|-- LICENSE
|-- pyproject.toml
|-- requirements.txt
|-- requirements-offline.txt
|-- docs/
|   |-- ARCHITECTURE_OVERVIEW.md
|   |-- DIRECTORY_LAYOUT.md
|   |-- DATA_MODEL.md
|   |-- MODULE_BREAKDOWN.md
|   |-- GUI_SPECIFICATIONS.md
|   |-- DELIVERABLES.md
|   |-- ROADMAP_PLUGINS.md
|   |-- REFERENCES.md
|   |-- formulas/
|   |-- accessibility/
|   |-- offline_verification/
|-- src/
|   |-- imbizo/
|       |-- main.py
|       |-- app/
|       |-- audio/
|       |-- core/
|       |   |-- project.py
|       |   |-- annotation.py
|       |   |-- morphology.py
|       |   |-- metrics.py
|       |   |-- export.py
|       |   |-- provenance.py
|       |   |-- security.py
|       |   |-- io/
|       |   |-- lid/
|       |-- domain/
|       |-- exporters/
|       |-- gui/
|       |-- i18n/
|       |-- importers/
|       |-- lid/
|       |-- metrics/
|       |-- morphology/
|       |-- persistence/
|       |-- plugins/
|       |-- resources/
|       |-- services/
|-- tests/
|-- scripts/
|-- packaging/
|-- examples/
|-- third_party/
|-- tools/
```

Top-level purposes:

- `PRINCIPLES.md`: constitutional design principles.
- `README.md`: humanities-facing user documentation.
- `INSTALL_OFFLINE.md`: offline installation and verification guide.
- `CITATION.cff`: software citation metadata.
- `LICENSE`: GPLv3-or-later license notice.
- `docs/`: design, formulas, accessibility, offline verification, roadmap, and
  references.
- `src/imbizo/core/`: stable core API matching the deliverable module names.
- `src/imbizo/services/`: application service orchestration.
- `src/imbizo/persistence/`: SQLite schema and repositories.
- `src/imbizo/importers/` and `src/imbizo/exporters/`: local interoperability
  with ELAN, Praat, spreadsheets, JSON, HTML, PDF, and quotation extracts.
- `src/imbizo/resources/i18n/`: externalized UI strings.
- `src/imbizo/plugins/`: optional local plug-in interfaces.
- `tests/`: offline pytest coverage.
- `scripts/`: offline bundle creation, packaging, and verification scripts.

Per-project storage convention:

```text
project/
|-- project.sqlite
|-- project.json
|-- media/
|-- transcripts/
|-- dictionaries/
|-- imports/
|-- exports/
|-- logs/provenance.jsonl
|-- cache/
```

# Deliverable 3 — Data Model

The complete SQLite schema lives in `src/imbizo/persistence/migrations.py` and
is expanded in `docs/DATA_MODEL.md`. It includes project metadata, languages,
participants, speakers, scenes, import batches, media assets, transcript
documents, segments, tokens, annotations, tags, morphology dictionaries,
morpheme splits, LID runs, LID suggestions, provenance records, metric runs,
metric results, and export records.

Representative schema excerpt:

```sql
CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    token_id TEXT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    segment_id TEXT NULL REFERENCES segments(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    matrix_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    embedded_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    switch_type TEXT NULL,
    linguistic_status TEXT NULL,
    trigger_text TEXT NOT NULL DEFAULT '',
    researcher_confidence INTEGER NULL,
    auto_confidence REAL NULL,
    memo TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((token_id IS NOT NULL AND segment_id IS NULL)
        OR (token_id IS NULL AND segment_id IS NOT NULL))
);
```

Project export JSON follows draft 2020-12 and includes annotations,
provenance, and metric snapshots. Pydantic v2 mirrors are implemented in
`src/imbizo/domain/pydantic_models.py`.

```python
class ProjectExportAnnotation(BaseModel):
    """Code-switching annotation object in project JSON export."""

    id: str = Field(description="Stable annotation identifier.")
    token_id: str | None = Field(default=None, description="Target token identifier.")
    segment_id: str | None = Field(default=None, description="Target segment identifier.")
    source: Literal["manual", "auto", "imported"] = Field(description="Annotation origin.")
    status: Literal["active", "rejected", "superseded"] = Field(default="active")
    language_id: str | None = Field(default=None)
    matrix_language_id: str | None = Field(default=None)
    embedded_language_id: str | None = Field(default=None)
```

Worked example, fictional isiZulu-English interview:

```json
{
  "project": {"title": "Durban youth interview", "researcher": "Dr. M."},
  "languages": [
    {"id": "lang-eng", "code": "eng", "name": "English"},
    {"id": "lang-zul", "code": "zul", "name": "isiZulu"}
  ],
  "segments": [
    {"id": "u1", "text_original": "I went ekhaya yesterday."},
    {"id": "u2", "text_original": "Ngiyabonga for helping me."},
    {"id": "u3", "text_original": "The class ibinzima today."},
    {"id": "u4", "text_original": "Sizobona tomorrow at school."},
    {"id": "u5", "text_original": "My teacher uthe I must read."}
  ],
  "annotations": [
    {"token_id": "u1-t1", "language_id": "lang-eng", "source": "manual"},
    {"token_id": "u1-t3", "language_id": "lang-zul", "source": "manual", "switch_type": "intra_sentential"},
    {"token_id": "u2-t1", "language_id": "lang-zul", "source": "manual"},
    {"token_id": "u2-t2", "language_id": "lang-eng", "source": "manual", "linguistic_status": "alternation"}
  ]
}
```

# Deliverable 4 — Module Breakdown

Minimum modules and implementation locations:

| Required module | Implementation | Responsibility | Test strategy |
| --- | --- | --- | --- |
| `core.project` | `src/imbizo/core/project.py` | Project folders, metadata, zip import/export. | Create/open/reopen smoke tests. |
| `core.io.audio` | `src/imbizo/core/io/audio.py` | Audio metadata, waveform cache, playback state. | WAV inspection and cache unit tests. |
| `core.io.eaf` | `src/imbizo/core/io/eaf.py` | ELAN EAF import/export. | EAF round-trip unit tests. |
| `core.io.textgrid` | `src/imbizo/core/io/textgrid.py` | Praat TextGrid import/export. | TextGrid interval tests. |
| `core.io.tabular` | `src/imbizo/core/io/tabular.py` | CSV/TSV/JSON/XLSX/ODS import. | Fixture imports. |
| `core.lid.baseline` | `src/imbizo/core/lid/baseline.py` | fastText-compatible baseline with fallback. | Missing-model fallback tests. |
| `core.lid.afrolid_stub` | `src/imbizo/core/lid/afrolid_stub.py` | Optional AfroLID boundary. | Availability/error tests. |
| `core.lid.masklid` | `src/imbizo/core/lid/masklid.py` | MaskLID-style suggestions. | Multilingual token fixture tests. |
| `core.annotation` | `src/imbizo/core/annotation.py` | Annotation model and persistence. | Save/effective annotation tests. |
| `core.morphology` | `src/imbizo/core/morphology.py` | Dictionaries and morpheme splits. | Suggestion and persistence tests. |
| `core.metrics` | `src/imbizo/core/metrics.py` | M-index, I-index, burstiness, KWIC, trigger tables. | Formula and property tests. |
| `core.export` | `src/imbizo/core/export.py` | Local CSV/XLSX/JSON/EAF/TextGrid/HTML/PDF/quotation exports. | File creation and citation sidecar tests. |
| `core.provenance` | `src/imbizo/core/provenance.py` | Append-only JSONL provenance. | Log write/read tests. |
| `core.security` | `src/imbizo/core/security.py` | Export warnings, AES-256 encryption, delete-and-verify. | Encryption round-trip and deletion tests. |
| `gui.*` | `src/imbizo/gui/` | Main window and screen widgets. | Model-level tests; manual PySide6 QA. |
| `i18n.translations` | `src/imbizo/i18n/translations.py` | Externalized strings. | Fallback lookup tests. |
| `plugins.api` | `src/imbizo/plugins/` | Optional provider protocols. | Registry tests. |

# Deliverable 5 — GUI Screen Specifications

Main window:

```text
Menu and toolbar
Project navigator | Tabs: Annotation / Spreadsheet / Timeline / Metrics / Settings
Language legend
Status bar
```

Annotation editor:

- Waveform band with local peaks and playhead.
- Transcript pane with original and optional normalized text.
- Token annotation grid.
- Memo/provenance/morpheme side pane.
- Automatic labels show source `auto`, layer, confidence, and accept/override
  affordances. Manual labels use stronger visual styling and are effective.

Spreadsheet view:

- Excel-like grid for token/segment annotation.
- Supports filtering, copy/paste-compatible tabular review, and bulk edit.

Timeline view:

- ELAN-like time ruler, waveform lane, speaker lanes, language spans, and
  switch markers (Wittenburg et al., 2006).

Metrics dashboard:

- Metric selector, scope selector, formula panel, result table, export action,
  and warnings when auto labels are included.

Project settings:

- Metadata, languages, participants, ethics/CARE acknowledgement, dictionaries,
  accessibility, and optional plugin state.

Keyboard and accessibility:

- Standard shortcuts for project open/save/import/export, find, undo/redo, font
  size, and playback.
- Color is never the only signal; source labels are text as well as style.
- Timeline data has table equivalents.

# Deliverable 6 — Core Source Code For The MVP

Runnable source code is implemented under `src/imbizo/`. The entry point is:

```bash
PYTHONPATH=src python -m imbizo.main --help
```

Core code includes:

- `src/imbizo/main.py`
- `src/imbizo/core/project.py`
- `src/imbizo/core/io/eaf.py`
- `src/imbizo/core/io/textgrid.py`
- `src/imbizo/core/lid/baseline.py`
- `src/imbizo/core/lid/masklid.py`
- `src/imbizo/core/lid/afrolid_stub.py`
- `src/imbizo/core/annotation.py`
- `src/imbizo/core/morphology.py`
- `src/imbizo/core/metrics.py`
- `src/imbizo/core/export.py`
- `src/imbizo/core/provenance.py`
- `src/imbizo/core/security.py`
- `src/imbizo/gui/main_window.py`
- `src/imbizo/gui/widgets/annotation_editor.py`

The code is real Python, not pseudocode. Tests are in `tests/unit/`.

# Deliverable 7 — Documentation For Humanities Researchers

`README.md` explains the tool for researchers rather than developers.

Your first project:

1. Create a local project folder.
2. Import a fictional isiZulu-English transcript.
3. Open the annotation editor.
4. Label tokens manually.
5. Run local LID suggestions if desired.
6. Compute M-index, I-index, and burstiness.
7. Export CSV/XLSX for analysis and HTML/PDF for review.
8. Cite the software using `CITATION.cff`.

Glossary:

- Matrix Language: the language providing the main grammatical frame
  (Myers-Scotton, 1993).
- Embedded Language: a language inserted into that frame (Myers-Scotton,
  2002).
- M-index: distributional diversity of languages in a corpus (Barnett et al.,
  2000).
- I-index: proportion of possible token boundaries that are switch points
  (Guzman et al., 2017).
- Burstiness: clustering of switch events over token intervals (Goh &
  Barabasi, 2008).

# Deliverable 8 — Offline Installation Guide

`INSTALL_OFFLINE.md` provides Windows and Debian/Ubuntu instructions. The
connected-machine bundle script is:

```bash
python scripts/create_offline_bundle.py imbizo-offline-bundle --include-fasttext-lid
```

Offline verification:

```bash
PYTHONPATH=src python scripts/verify_offline_install.py
PYTHONPATH=src python scripts/verify_no_network.py
PYTHONPATH=src pytest -q
```

# Deliverable 9 — PRINCIPLES.md

`PRINCIPLES.md` is the codebase constitution. It explains offline-first
research, data sovereignty, automation as auxiliary, Bantu morphology,
deferred ASR, refusal of default cloud LLM dependencies, CARE principles,
decolonial computing, citable software, and the GPLv3-or-later license choice
(Carroll et al., 2020; Ali, 2016; Risam, 2018; Smith et al., 2016).

# Deliverable 10 — Roadmap And References

## 10a. Roadmap

| Plug-in | Dependency footprint | Offline feasibility | Ethical review | Optional? |
| --- | --- | --- | --- | --- |
| Local ASR: Whisper.cpp, Vosk, Coqui | Medium to high model files | Good with local bundles | Consent and error review needed | Must remain optional |
| AfroLID bundle | Medium neural model resources | Good with local install | Language coverage caveats | Must remain optional |
| SADiLaR morphology | Small to medium dictionaries/analyzers | Good | Community/resource licensing review | Must remain optional |
| Additional languages | Small label/dictionary resources | Excellent | Community naming and orthography review | Must remain optional |
| Localized UIs | Small translation files | Excellent | Translation review | Must remain optional but encouraged |
| Optional LLM assistance | Potentially high, especially cloud | Local-only preferred; cloud discouraged | Full ethics and consent review | Must remain optional |

## 10b. Master References

Adebara, I., Elmadany, A., Abdul-Mageed, M., & Alcoba Inciarte, A. (2022).
AfroLID: A neural language identification tool for African languages. EMNLP
2022. https://aclanthology.org/2022.emnlp-main.128/

Al-Rfou, R., Perozzi, B., & Skiena, S. (2013). Polyglot: Distributed word
representations for multilingual NLP. CoNLL 2013.

Ali, S. M. (2016). A brief introduction to decolonial computing. XRDS:
Crossroads, 22(4).

Auer, P. (Ed.). (1998). Code-switching in conversation: Language, interaction
and identity. Routledge.

Barnett, R., Codo, E., Eppler, E., Forcadell, M., Gardner-Chloros, P., van
Hout, R., et al. (2000). The LIDES Coding Manual. International Journal of
Bilingualism, 4(2).

Boersma, P., & Weenink, D. (2024). Praat: Doing phonetics by computer.
https://www.fon.hum.uva.nl/praat/

Carroll, S. R., Garba, I., Figueroa-Rodriguez, O. L., Holbrook, J., Lovett,
R., Materechera, S., et al. (2020). The CARE Principles for Indigenous Data
Governance. Data Science Journal, 19(1).

Chue Hong, N. P., et al. (2022). FAIR Principles for Research Software
(FAIR4RS Principles). Research Data Alliance.

Clyne, M. (2003). Dynamics of language contact. Cambridge University Press.

Cozien, C. (2020). Code-switching among bilingual speakers of Cape Muslim
Afrikaans and South African English in the Bo-Kaap, Cape Town. MA thesis,
University of Cape Town.

Eiselen, R., & Puttkammer, M. J. (2014). Developing text resources for ten
South African languages. LREC 2014.

Goh, K.-I., & Barabasi, A.-L. (2008). Burstiness and memory in complex
systems. EPL, 81(4).

Guzman, G. A., Ricard, J., Serigos, J., Bullock, B. E., & Toribio, A. J.
(2017). Metrics for modeling code-switching across corpora. INTERSPEECH 2017.

Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2017). Bag of tricks for
efficient text classification. EACL 2017.

Kargaran, A. H., Yvon, F., & Schutze, H. (2024). MaskLID: Code-switching
language identification through iterative masking. ACL 2024.

Kodali, P., Goel, A., Choudhury, M., Shrivastava, M., & Kumaraguru, P. (2022).
SyMCoM - Syntactic measure of code mixing: A study of English-Hindi
code-mixing. Findings of ACL 2022.

Mabokela, R., & Schlippe, T. (2022). A sentiment corpus for South African
under-resourced languages in a multilingual context. SIGUL @ LREC 2022.

Mahomed, S., Maritz, J., Scholtz, L., Barnard, E., & Heerden, C. van. (2019).
Prevalence of code mixing in semi-formal patient communication in low-resource
languages of South Africa. arXiv:1911.05636.

Muysken, P. (2000). Bilingual speech: A typology of code-mixing. Cambridge
University Press.

Myers-Scotton, C. (1993). Duelling languages: Grammatical structure in
codeswitching. Oxford University Press.

Myers-Scotton, C. (2002). Contact linguistics: Bilingual encounters and
grammatical outcomes. Oxford University Press.

Nel, J. H. (2012). Grammatical and socio-pragmatic aspects of conversational
code switching by Afrikaans-English bilingual children. MA thesis,
Stellenbosch University.

Poplack, S. (1980). Sometimes I'll start a sentence in Spanish y termino en
espanol. Linguistics, 18(7/8).

Risam, R. (2018). New digital worlds: Postcolonial digital humanities in
theory, praxis, and pedagogy. Northwestern University Press.

Slabbert, S., & Myers-Scotton, C. (1997). The structure of Tsotsitaal and
Iscamtho: Code-switching and in-group identity in South African townships.
Linguistics, 35(2).

Smith, A. M., Katz, D. S., Niemeyer, K. E., & FORCE11 Software Citation Working
Group. (2016). Software citation principles. PeerJ Computer Science, 2:e86.

Stell, G. (2010). Ethnicity in linguistic variation: White and Coloured
identities in Afrikaans-English code-switching. Pragmatics, 20(3).

Vandeghinste, V., et al. (2025). AfroCS-xs: Creating a compact, high-quality,
human-validated code-switched dataset for African languages. ACL 2025.

Van der Westhuizen, E., & Niesler, T. R. (2018). A first South African corpus
of multilingual code-switched soap opera speech. LREC 2018.

Wittenburg, P., Brugman, H., Russel, A., Klassmann, A., & Sloetjes, H. (2006).
ELAN: A professional framework for multimodality research. LREC 2006.

Yilmaz, E., Biswas, A., Van der Westhuizen, E., De Wet, F., & Niesler, T.
(2018). Building a unified code-switching ASR system for South African
languages. INTERSPEECH 2018. arXiv:1807.10949.
