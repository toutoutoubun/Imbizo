# v1.0 Deliverable 7 — Reports and Exports

This deliverable defines v1.0 export additions for noun-class, concord,
loanword-integration, and 4-M/MLF audit evidence. All exports are local files
and remain reproducible from the project SQLite database, dictionary snapshots,
and provenance log.

## 1. Updated CSV / XLSX Export Schemas

### `tokens_export.csv`

```csv
token_id,segment_id,sort_order,token_text,normalized_text,char_start,char_end,language_id,matrix_language_id,embedded_language_id,nc_class,nc_prefix,nc_source,four_m_type,four_m_source,integration_score
```

New v1.0 column documentation:

| Column | Data-dictionary comment |
| --- | --- |
| `nc_class` | Optional noun-class number assigned or accepted for this token; blank means not reviewed. |
| `nc_prefix` | Surface prefix used as noun-class evidence, preserved as transcribed or manually split. |
| `nc_source` | Review source for noun-class value: `manual`, `suggested-accepted`, or `suggested-overridden`. |
| `four_m_type` | Optional 4-M morpheme category: `content`, `early_system`, `bridge_late_system`, or `outsider_late_system`. |
| `four_m_source` | Review source for the 4-M value: `manual`, `suggested-accepted`, or `suggested-overridden`. |
| `integration_score` | Transparent weighted score in `[0,1]` summarizing concord, noun-class, frequency, and review evidence for a non-host stem. |

### `annotations_export.xlsx`

The existing annotation worksheet gains the same v1.0 columns as
`tokens_export.csv`:

```text
nc_class
nc_prefix
nc_source
four_m_type
four_m_source
integration_score
```

New worksheet: `concord_links`

```csv
id,segment_id,controller_token_id,concord_token_id,concord_type,controller_nc_class,expected_form,observed_form,agreement_status,source,confidence,dictionary_snapshot_id,note,created_at,updated_at
```

New worksheet: `mlf_audit`

```csv
id,segment_id,verdict,matrix_language_id,embedded_language_id,system_morpheme_count,outsider_late_system_morpheme_count,content_morpheme_switch_count,confirmed_concord_link_count,reviewed_concord_link_count,integration_score,source,checker_version,explanation,created_at,updated_at
```

Worksheet column documentation:

| Column | Data-dictionary comment |
| --- | --- |
| `concord_type` | Concord category: subject, object, adjectival, possessive, relative, or demonstrative (`SC`, `OC`, `AC`, `PC`, `RC`, `DEM`). |
| `controller_nc_class` | Noun class of the head/controller token, when reviewed. |
| `expected_form` | Local dictionary marker suggested for the concord relation; blank if not generated. |
| `observed_form` | Surface form observed in the transcript. |
| `agreement_status` | Researcher review status: `confirmed`, `mismatch`, `uncertain`, or `not_applicable`. |
| `dictionary_snapshot_id` | Per-project dictionary snapshot used to generate or review the relation. |
| `verdict` | Advisory MLF audit status: `consistent`, `mixed`, or `insufficient_data`. |
| `checker_version` | Local checker version used to produce the audit row. |
| `explanation` | Plain-language explanation suitable for appendices and audit trails. |

### `project_snapshot.json`

Augmented JSON paths:

```json
{
  "tokens[*].nc_class": "Optional noun-class number.",
  "tokens[*].nc_prefix": "Optional surface noun-class prefix.",
  "tokens[*].nc_source": "Review source for noun-class value.",
  "tokens[*].four_m_type": "Optional 4-M morpheme category.",
  "tokens[*].four_m_source": "Review source for 4-M value.",
  "tokens[*].integration_score": "Optional transparent loanword-integration score.",
  "concord_links[*]": "Reviewed concord agreement records.",
  "four_m_audits[*]": "Per-utterance MLF audit records.",
  "noun_class_dictionaries[*]": "Per-project dictionary version snapshots."
}
```

## 2. HTML Report — Loanword Integration Profile

Template file:
`src/imbizo/resources/templates/reports/loanword_integration.html.j2`

The template renders a project header, dictionary versions, one section per
non-host stem, inline SVG noun-class distributions, inline SVG integration
histograms, example utterances, a methods note, and a reusable formula
transparency block. It is self-contained: no remote fonts, scripts, images, or
CDNs. The inline SVG charts include `<title>` and `<desc>` elements for
accessibility. The methods note cites borrowing and code-mixing frameworks used
to interpret integration evidence (Poplack, 1980; Muysken, 2000;
Myers-Scotton, 2002).

Expected context keys:

```json
{
  "project": {"title": "Project title", "researcher": "Researcher", "date": "YYYY-MM-DD"},
  "dictionary_versions": [{"label": "NC zul", "version": "0.1.0", "source": "Poulos & Msimang (1998)"}],
  "stems": [
    {
      "surface": "i-laptop",
      "language_of_origin": "eng",
      "total_occurrences": 12,
      "class_distribution": [{"class_label": "9", "count": 7, "percent": 58, "bar_width": 244}],
      "integration_histogram": [{"label": "0.8-1.0", "percent": 40, "height": 48}],
      "examples": [{"timestamp": "00:01:12", "speaker_id": "S1", "context": "Ngithenge i-laptop entsha izolo."}]
    }
  ],
  "formula": {"weights": {"concord": 0.35, "noun_class": 0.35, "frequency": 0.20, "researcher_review": 0.10}},
  "imbizo_version": "v1.0",
  "project_schema_version": "1.0.0"
}
```

## 3. HTML Report — MLF Audit

Template file:
`src/imbizo/resources/templates/reports/mlf_audit.html.j2`

The template renders project metadata, summary counts, a per-utterance audit
table, mini inline SVG 4-M distribution bars, drill-down sections for `mixed`
utterances, a methods note, and the shared formula transparency partial. It is
self-contained and print-friendly. The methods note cites the System Morpheme
Principle and 4-M model sources while making clear that the verdict is advisory
(Myers-Scotton, 1993; Myers-Scotton, 2002; Jake, Myers-Scotton & Gross, 2002).

Expected context keys:

```json
{
  "project": {"title": "Project title", "researcher": "Researcher", "date": "YYYY-MM-DD"},
  "summary": {"consistent": 3, "mixed": 1, "insufficient_data": 4},
  "utterances": [
    {
      "id": "u1",
      "timestamp": "00:01:12",
      "speaker_id": "S1",
      "four_m_distribution": [{"type_class": "content", "x": 0, "width": 80}],
      "verdict": "consistent",
      "recommended_action": "No immediate review required."
    }
  ],
  "mixed_utterances": [
    {
      "id": "u2",
      "timestamp": "00:02:44",
      "speaker_id": "S2",
      "narrative": "System morphemes point to more than one language.",
      "evidence": [{"token_id": "t1", "surface": "u-", "language_id": "zul", "four_m_type": "outsider_late_system", "note": "review"}]
    }
  ],
  "formula": {"weights": {"concord": 0.35, "noun_class": 0.35, "frequency": 0.20, "researcher_review": 0.10}},
  "dictionary_versions": [],
  "imbizo_version": "v1.0",
  "project_schema_version": "1.0.0"
}
```

## 4. PDF Rendering

Each HTML report is rendered to PDF through WeasyPrint using only local,
already-rendered HTML and bundled templates. The PDF renderer rejects `http://`
and `https://` resources through a local-only URL fetcher, so no network calls
occur during rendering.

Skeleton implemented at:
`src/imbizo/core/export/pdf.py`

```python
def render_report_to_pdf(template_name: str, context: dict, out_path: Path) -> None: ...
```

`template_name` is a bundled path such as
`reports/loanword_integration.html.j2` or `reports/mlf_audit.html.j2`.

## 5. Formula Transparency Partial

Template file:
`src/imbizo/resources/templates/partials/formula_transparency.html.j2`

The partial displays:

- integration-score weights actually used
- dictionary versions actually used
- Imbizo-CS version
- project schema version
- reproducibility statement:
  “To reproduce this report, open the exported project zip in Imbizo-CS v1.0
  and run Reports → Loanword Integration.”

## 6. Quotation Extracts

`quotations.csv` supports qualitative write-up and copy-pasteable citation keys.

```csv
utterance_id,start_time,end_time,speaker_id,raw_text,normalized_text,matrix_language,contains_loanword,loanword_count,integration_score_max,researcher_memo,suggested_citation_key
```

Column documentation:

| Column | Data-dictionary comment |
| --- | --- |
| `utterance_id` | Stable utterance or segment identifier. |
| `start_time` | Segment start timestamp, when available. |
| `end_time` | Segment end timestamp, when available. |
| `speaker_id` | Local speaker identifier from the project database. |
| `raw_text` | Original transcript text; never overwritten by normalization. |
| `normalized_text` | Optional non-destructive normalized text. |
| `matrix_language` | Researcher-assigned Matrix Language for the utterance, if any. |
| `contains_loanword` | Boolean flag indicating at least one reviewed non-host stem. |
| `loanword_count` | Count of reviewed non-host stems in the utterance. |
| `integration_score_max` | Maximum integration score among reviewed non-host stems in the utterance. |
| `researcher_memo` | Free-text memo selected for quotation export. |
| `suggested_citation_key` | Copy-pasteable key in the pattern `{project_short_name}_{speaker_id}_{utterance_id}`. |

Sample output:

```text
durban_cs_S1_u001
```

