# v1.5 Deliverable 7 - Reports and Exports

This deliverable defines v1.5 export schemas, report templates, and companion
validation artifacts for sister-language disambiguation, triggered switching,
mixed-code variety spans, phonological integration evidence, LIDES, CHAT/CLAN,
and community-review packets. All exports are local-only and self-contained.

## 1. Updated CSV / XLSX Export Schemas

### `tokens_export.csv`

```csv
column,documentation
sister_lang_confidence,"Advisory confidence in [0,1] for a sister-language disambiguation suggestion; blank if no tie was reviewed."
sister_lang_evidence,"Comma-separated evidence codes from the active sister-language dictionary, for example morph_ndi_xho or context_tok3_xho."
trigger_role,"Reviewed trigger role for this token: none, trigger, triggered, or blank when not annotated."
mixed_code_variety,"Accepted mixed-code variety span label for this token, such as tsotsitaal, iscamtho, kaaps, or sabela; blank when absent."
phon_integration_score,"Borrowing Integration Score v2 in [0,1], using project-defined morphology, concord, frequency, and phonology weights."
```

The CSV keeps v1.0 columns unchanged and appends these v1.5 fields after
`integration_score` where that v1.0 export column exists.

### `annotations_export.xlsx`

The workbook keeps MVP and v1.0 sheets and adds:

```csv
sheet,column,documentation
tokens,sister_lang_confidence,"Advisory confidence for sister-language evidence."
tokens,sister_lang_evidence,"Evidence codes used to support or preserve ambiguity."
tokens,trigger_role,"Token role in a confirmed or manually coded trigger relation."
tokens,mixed_code_variety,"Accepted mixed-code variety span label touching this token."
tokens,phon_integration_score,"Integration v2 score with optional phonological evidence."
trigger_links,head_token_id,"Token that provides the candidate trigger context."
trigger_links,triggered_token_id,"Token after the switch boundary associated with the trigger context."
trigger_links,trigger_type,"Clyne-style trigger type: proper_noun, borrowing, cognate, discourse_marker, or project-local value."
trigger_links,confidence,"Advisory confidence assigned before researcher confirmation."
trigger_links,source,"manual, suggested-accepted, suggested-overridden, or imported."
trigger_links,note,"Researcher memo explaining the trigger relation or rejection context."
mixed_code_spans,id,"Stable local span identifier."
mixed_code_spans,start_token_id,"First token in the mixed-code span."
mixed_code_spans,end_token_id,"Last token in the mixed-code span."
mixed_code_spans,variety,"Accepted variety label."
mixed_code_spans,confidence,"Advisory lexical-density confidence."
mixed_code_spans,source,"manual, suggested-accepted, suggested-overridden, or imported."
mixed_code_spans,note,"Researcher memo; required for sensitive or contested spans."
phonological_features,id,"Stable local feature identifier."
phonological_features,token_id,"Token to which the phonological evidence applies."
phonological_features,feature_type,"vowel_epenthesis, consonant_cluster_simplification, tonal_reassignment, stress_pattern_shift, click_reduction, or project-local value."
phonological_features,value,"Observed value or dictionary cue."
phonological_features,source,"manual, suggested-accepted, suggested-overridden, or imported."
phonological_features,note,"Researcher note, uncertainty statement, or transcription caveat."
community_reviews,id,"Stable local community-review identifier."
community_reviews,target_kind,"Reviewed target type, such as dictionary_entry or phonological_feature."
community_reviews,target_id,"Local identifier of the reviewed target."
community_reviews,reviewer_alias,"Reviewer-chosen name, initials, or pseudonym."
community_reviews,comment,"Human-readable review comment."
community_reviews,status,"pending, accepted, rejected, or superseded."
community_reviews,signature_hash,"SHA-256 hash of the review-packet signature or attestation."
```

### `project_snapshot.json`

```text
$.tokens[*].sister_lang_confidence
$.tokens[*].sister_lang_evidence
$.tokens[*].trigger_role
$.tokens[*].mixed_code_variety
$.tokens[*].phon_integration_score
$.trigger_links[*].head_token_id
$.trigger_links[*].triggered_token_id
$.trigger_links[*].trigger_type
$.trigger_links[*].confidence
$.trigger_links[*].source
$.trigger_links[*].note
$.mixed_code_spans[*].id
$.mixed_code_spans[*].start_token_id
$.mixed_code_spans[*].end_token_id
$.mixed_code_spans[*].variety
$.mixed_code_spans[*].confidence
$.mixed_code_spans[*].source
$.mixed_code_spans[*].note
$.phonological_features[*].id
$.phonological_features[*].token_id
$.phonological_features[*].feature_type
$.phonological_features[*].value
$.phonological_features[*].source
$.phonological_features[*].note
$.community_reviews[*].id
$.community_reviews[*].target_kind
$.community_reviews[*].target_id
$.community_reviews[*].reviewer_alias
$.community_reviews[*].comment
$.community_reviews[*].status
$.community_reviews[*].signature_hash
$.metadata.dictionary_versions.sister_lang
$.metadata.dictionary_versions.triggers
$.metadata.dictionary_versions.mixed_code
$.metadata.dictionary_versions.phonology
$.metadata.integration_v2_weights
```

## 2. New HTML Report - Trigger Profile

`templates/reports/trigger_profile.html.j2`

```jinja
<!doctype html>
<html lang="{{ locale|default('en') }}">
<head>
  <meta charset="utf-8">
  <title>{{ project.title }} - Trigger Profile</title>
  <style>
    :root { --fg:#111; --bg:#fff; --line:#555; --soft:#f4f4f4; --accent:#005fcc; --warn:#6b4e00; }
    body { background:var(--bg); color:var(--fg); font-family:Arial, sans-serif; line-height:1.45; margin:2rem; }
    table { border-collapse:collapse; width:100%; margin:1rem 0; }
    th, td { border:1px solid var(--line); padding:.4rem; text-align:left; vertical-align:top; }
    th { background:var(--soft); }
    .meta, .methods, .formula { border:1px solid var(--line); padding:1rem; margin:1rem 0; }
    .bar { fill:var(--accent); }
    .axis { stroke:var(--line); stroke-width:1; }
    @media print { body { margin:1cm; } a::after { content:""; } }
  </style>
</head>
<body>
  <header>
    <h1>Trigger Profile</h1>
    <div class="meta">
      <p><strong>Project:</strong> {{ project.title }}</p>
      <p><strong>Researcher:</strong> {{ project.researcher }}</p>
      <p><strong>Date:</strong> {{ generated_at }}</p>
      <p><strong>Dictionary versions:</strong> {{ dictionary_versions.triggers|default({}) }}</p>
    </div>
  </header>

  <section>
    <h2>Trigger Counts by Speaker and Scene</h2>
    <table aria-label="Trigger counts by speaker and scene">
      <thead><tr><th>Speaker</th><th>Scene</th><th>Trigger type</th><th>Confirmed count</th></tr></thead>
      <tbody>
      {% for row in trigger_counts %}
        <tr><td>{{ row.speaker_id }}</td><td>{{ row.scene_id }}</td><td>{{ row.trigger_type }}</td><td>{{ row.count }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Top Trigger Tokens</h2>
    <table aria-label="Top trigger tokens with example utterances">
      <thead><tr><th>Token</th><th>Type</th><th>Count</th><th>Example timestamp</th><th>Example utterance</th></tr></thead>
      <tbody>
      {% for item in top_triggers %}
        <tr>
          <td>{{ item.surface }}</td><td>{{ item.trigger_type }}</td><td>{{ item.count }}</td>
          <td>{{ item.timestamp }}</td><td>{{ item.example_utterance }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Trigger Density Timeline</h2>
    <svg role="img" width="760" height="180" viewBox="0 0 760 180">
      <title>Trigger density over interview duration</title>
      <desc>Bars show confirmed trigger counts per time bin. Suggested triggers are excluded unless explicitly requested.</desc>
      <line class="axis" x1="40" y1="150" x2="730" y2="150"></line>
      {% for bin in timeline_bins %}
        <rect class="bar" x="{{ 45 + loop.index0 * timeline_bar_width }}" y="{{ 150 - bin.height }}" width="{{ timeline_bar_width - 4 }}" height="{{ bin.height }}"></rect>
      {% endfor %}
    </svg>
  </section>

  {% include "partials/formula_transparency.html.j2" %}

  <section class="methods">
    <h2>Methods Note</h2>
    <p>Trigger candidates are interpreted as reviewed contexts following Clyne's trigger hypothesis, not as proof of speaker intention or causality (Clyne, 1967, 2003). Only confirmed trigger links are counted by default.</p>
  </section>
</body>
</html>
```

## 3. New HTML Report - Mixed-Code Variety Profile

`templates/reports/mixed_code_profile.html.j2`

```jinja
<!doctype html>
<html lang="{{ locale|default('en') }}">
<head>
  <meta charset="utf-8">
  <title>{{ project.title }} - Mixed-Code Variety Profile</title>
  <style>
    :root { --fg:#111; --bg:#fff; --line:#555; --soft:#f4f4f4; --accent:#005fcc; --caution:#fff4c2; }
    body { background:var(--bg); color:var(--fg); font-family:Arial, sans-serif; line-height:1.45; margin:2rem; }
    table { border-collapse:collapse; width:100%; margin:1rem 0; }
    th, td { border:1px solid var(--line); padding:.4rem; text-align:left; }
    th { background:var(--soft); }
    .caveats { background:var(--caution); border:2px solid var(--line); padding:1rem; margin:1rem 0; }
    .methods, .formula, .meta { border:1px solid var(--line); padding:1rem; margin:1rem 0; }
    @media print { body { margin:1cm; } }
  </style>
</head>
<body>
  <header>
    <h1>Mixed-Code Variety Profile</h1>
    <div class="meta">
      <p><strong>Project:</strong> {{ project.title }}</p>
      <p><strong>Generated:</strong> {{ generated_at }}</p>
      <p><strong>Active variety dictionaries:</strong> {{ dictionary_versions.mixed_code|default({}) }}</p>
    </div>
  </header>

  <section class="caveats">
    <h2>Caveats from Active Dictionaries</h2>
    {% for variety in varieties %}
      <h3>{{ variety.name }}</h3>
      <p>{{ variety.caveats }}</p>
    {% endfor %}
  </section>

  <section>
    <h2>Span Counts and Durations</h2>
    <table aria-label="Mixed-code span counts and durations by variety">
      <thead><tr><th>Variety</th><th>Span count</th><th>Total duration</th><th>Mean confidence</th></tr></thead>
      <tbody>
      {% for row in variety_summary %}
        <tr><td>{{ row.variety }}</td><td>{{ row.count }}</td><td>{{ row.total_duration }}</td><td>{{ row.mean_confidence }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Speaker x Variety Matrix</h2>
    <table aria-label="Speaker by variety matrix">
      <thead>
        <tr><th>Speaker</th>{% for variety in matrix.varieties %}<th>{{ variety }}</th>{% endfor %}</tr>
      </thead>
      <tbody>
      {% for row in matrix.rows %}
        <tr><td>{{ row.speaker_id }}</td>{% for count in row.counts %}<td>{{ count }}</td>{% endfor %}</tr>
      {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Example Excerpts</h2>
    {% for example in examples %}
      <article>
        <h3>{{ example.variety }} - {{ example.timestamp }} - {{ example.speaker_id }}</h3>
        <p>{{ example.excerpt }}</p>
        <p><strong>Evidence:</strong> {{ example.evidence_forms|join(", ") }}</p>
      </article>
    {% endfor %}
  </section>

  {% include "partials/formula_transparency.html.j2" %}

  <section class="methods">
    <h2>Methods Note</h2>
    <p>Mixed-code reports summarize accepted span annotations and lexical evidence. They do not identify a speaker or whole text as a variety. Interpretation must consider speaker, setting, history, and local sociolinguistic context (Slabbert & Myers-Scotton, 1997; Hurst, 2008; McCormick, 2002; Mesthrie, 2008).</p>
  </section>
</body>
</html>
```

## 4. New HTML Report - Integration v2 Comparison

`templates/reports/integration_v2.html.j2`

```jinja
<!doctype html>
<html lang="{{ locale|default('en') }}">
<head>
  <meta charset="utf-8">
  <title>{{ project.title }} - Integration v2 Comparison</title>
  <style>
    :root { --fg:#111; --bg:#fff; --line:#555; --soft:#f4f4f4; --v1:#555; --v2:#005fcc; }
    body { background:var(--bg); color:var(--fg); font-family:Arial, sans-serif; line-height:1.45; margin:2rem; }
    table { border-collapse:collapse; width:100%; margin:1rem 0; }
    th, td { border:1px solid var(--line); padding:.4rem; text-align:left; vertical-align:top; }
    th { background:var(--soft); }
    .v1 { fill:var(--v1); } .v2 { fill:var(--v2); }
    .axis { stroke:var(--line); stroke-width:1; }
    .methods, .formula, .meta { border:1px solid var(--line); padding:1rem; margin:1rem 0; }
    @media print { body { margin:1cm; } }
  </style>
</head>
<body>
  <header>
    <h1>Integration v2 Comparison</h1>
    <div class="meta">
      <p><strong>Project:</strong> {{ project.title }}</p>
      <p><strong>Generated:</strong> {{ generated_at }}</p>
      <p><strong>Phonology dictionaries:</strong> {{ dictionary_versions.phonology|default({}) }}</p>
    </div>
  </header>

  <section>
    <h2>v2 Score Histogram</h2>
    <svg role="img" width="760" height="180" viewBox="0 0 760 180">
      <title>Histogram of Integration v2 scores</title>
      <desc>Bars show counts of tokens by phonologically-aware integration score bin.</desc>
      <line class="axis" x1="40" y1="150" x2="730" y2="150"></line>
      {% for bin in histogram_bins %}
        <rect class="v2" x="{{ 45 + loop.index0 * histogram_bar_width }}" y="{{ 150 - bin.height }}" width="{{ histogram_bar_width - 4 }}" height="{{ bin.height }}"></rect>
      {% endfor %}
    </svg>
  </section>

  <section>
    <h2>v1.0 vs v1.5 Scores</h2>
    <table aria-label="Side-by-side comparison of v1.0 and v1.5 integration scores">
      <thead><tr><th>Stem</th><th>Language of origin</th><th>v1.0 score</th><th>v1.5 score</th><th>Difference</th></tr></thead>
      <tbody>
      {% for row in score_comparison %}
        <tr>
          <td>{{ row.stem }}</td><td>{{ row.origin_language }}</td>
          <td>{{ row.v1_score }}</td><td>{{ row.v2_score }}</td><td>{{ row.difference }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Per-Stem Phonological Evidence</h2>
    {% for stem in stem_details %}
      <article>
        <h3>{{ stem.surface }}</h3>
        <p><strong>Score:</strong> {{ stem.v2_score }}</p>
        <ul>
        {% for feature in stem.phonological_features %}
          <li>{{ feature.feature_type }}: {{ feature.value }}{% if feature.note %} - {{ feature.note }}{% endif %}</li>
        {% endfor %}
        </ul>
      </article>
    {% endfor %}
  </section>

  {% include "partials/formula_transparency.html.j2" %}

  <section class="methods">
    <h2>Methods Note</h2>
    <p>Integration v2 is a transparent weighted score over morphology, concord, frequency, and reviewed phonological evidence. It supports sensitivity analysis rather than deciding borrowing status automatically (Poplack, 1980; Muysken, 2000; Mesthrie, 2002).</p>
  </section>
</body>
</html>
```

## 5. LIDES Exporter

`core/interop/lides.py` reference API:

```python
def to_lides(project: Project) -> str: ...
def validate_lides(text: str) -> ValidationReport: ...
```

Output format:

```text
# IMBIZO_LIDES 1.5
# reference: Barnett et al. (2000)
# project_id: <local id>
TOK    <utterance_id>    <position>    <token_id>    <surface>    <language>    <speaker_id>
XIMB   <token_id>        {"nc_class":9,"four_m_type":"content","trigger_role":"none",...}
```

The `TOK` rows provide the comparable code-switching view. `XIMB` sidecar rows
preserve Imbizo-specific fields so conversion to a shared format does not erase
local analysis.

Documented losses:

- Free-text memos may not round-trip into a LIDES-only tool.
- v1.5 mixed-code caveats and dictionary provenance require the `XIMB` sidecar.
- Integration v2 factors may be flattened unless the sidecar is retained.
- Community-review packet status is not a LIDES concept.

Companion artifact: `lides_validation_report.html`

```jinja
<!doctype html>
<html lang="{{ locale|default('en') }}">
<head><meta charset="utf-8"><title>LIDES Validation Report</title></head>
<body>
  <h1>LIDES Validation Report</h1>
  <p>Status: {{ "valid" if report.valid else "invalid" }}</p>
  <h2>Errors</h2><ul>{% for item in report.errors %}<li>{{ item }}</li>{% endfor %}</ul>
  <h2>Warnings</h2><ul>{% for item in report.warnings %}<li>{{ item }}</li>{% endfor %}</ul>
  <h2>Documented Losses</h2><ul>{% for item in report.documented_losses %}<li>{{ item }}</li>{% endfor %}</ul>
</body>
</html>
```

## 6. CHAT/CLAN Exporter

`core/interop/chat_clan.py` reference API:

```python
def to_chat(project: Project) -> str: ...
def validate_chat(text: str) -> ChatValidationReport: ...
```

CHAT header:

```text
@UTF8
@Begin
@Languages:    eng, zul
@Participants: S01 Participant, S02 Participant
@ID:           imbizo|<project_id>|<project_title>|
```

Mapping:

- Main tiers: `*S01:` contain readable utterance text.
- Dependent tiers: `%ximb:` contain JSON with token ids, language tags, noun
  class, 4-M, trigger role, mixed-code variety, and integration v2 fields.
- Sidecar JSON may be exported alongside the `.cha` file for tools that do not
  preserve unknown dependent tiers.

Documented losses:

- CHAT does not natively model all Imbizo v1.0/v1.5 linguistic fields.
- Some CLAN workflows may ignore `%ximb` tiers.
- Community-review and dictionary caveat data remain in sidecar/report files.
- Round-trip from CHAT back to full Imbizo project is not guaranteed.

Companion artifact: `chat_validation_report.html`

```jinja
<!doctype html>
<html lang="{{ locale|default('en') }}">
<head><meta charset="utf-8"><title>CHAT/CLAN Validation Report</title></head>
<body>
  <h1>CHAT/CLAN Validation Report</h1>
  <p>Status: {{ "valid" if report.valid else "invalid" }}</p>
  <h2>Errors</h2><ul>{% for item in report.errors %}<li>{{ item }}</li>{% endfor %}</ul>
  <h2>Warnings</h2><ul>{% for item in report.warnings %}<li>{{ item }}</li>{% endfor %}</ul>
  <h2>Documented Losses</h2><ul>{% for item in report.documented_losses %}<li>{{ item }}</li>{% endfor %}</ul>
</body>
</html>
```

## 7. Community-Review Packet Format

```text
review_packet.zip
|-- manifest.json
|-- diff_human_readable.md
|-- diff_machine_readable.json
|-- signature.sig
|-- README_FOR_REVIEWER.md
```

`manifest.json`:

```json
{
  "packet_id": "uuid",
  "source_project_id_hash": "sha256",
  "target_kinds": ["dictionary_entry", "phonological_feature"],
  "reviewer_alias": "ReviewerA",
  "timestamp": "2026-05-27T12:00:00Z",
  "imbizo_cs_version": "1.5.0",
  "dictionary_versions": {
    "sister_lang": {"zul_vs_xho": "0.1.0"},
    "triggers": {"eng": "0.1.0"},
    "mixed_code": {"tsotsitaal": "0.1.0"},
    "phonology": {"zul": "0.1.0"}
  }
}
```

`diff_human_readable.md` explains the proposed change in ordinary language.
`diff_machine_readable.json` stores structured add/update/reject operations.
`signature.sig` is a SHA-256 digest over canonicalized `manifest.json`,
`diff_human_readable.md`, and `diff_machine_readable.json`. It is not a remote
identity system; it is a local tamper-evidence mechanism. `README_FOR_REVIEWER.md`
explains how to inspect the packet offline, edit comments, and return it by USB.

## 8. Reproducibility Statement Extension

The shared formula-transparency partial should be extended as follows:

`templates/partials/formula_transparency.html.j2`

```jinja
<section class="formula" aria-labelledby="formula-transparency-heading">
  <h2 id="formula-transparency-heading">Formula Transparency and Reproducibility</h2>
  <p><strong>Imbizo-CS version:</strong> {{ imbizo_version }}</p>
  <p><strong>Project schema version:</strong> {{ schema_version }}</p>

  <h3>Dictionary Versions Used</h3>
  <dl>
    <dt>Sister-language dictionary versions used</dt>
    <dd>{{ dictionary_versions.sister_lang|default({}) }}</dd>
    <dt>Trigger dictionary versions used</dt>
    <dd>{{ dictionary_versions.triggers|default({}) }}</dd>
    <dt>Mixed-code dictionary versions used</dt>
    <dd>{{ dictionary_versions.mixed_code|default({}) }}</dd>
    <dt>Phonology dictionary versions used</dt>
    <dd>{{ dictionary_versions.phonology|default({}) }}</dd>
  </dl>

  <h3>Integration v2 weights used</h3>
  <table aria-label="Integration v2 weights">
    <thead><tr><th>Factor</th><th>Weight</th></tr></thead>
    <tbody>
    {% for factor, weight in integration_v2_weights.items() %}
      <tr><td>{{ factor }}</td><td>{{ weight }}</td></tr>
    {% endfor %}
    </tbody>
  </table>

  <p>To reproduce this report, open the exported project zip in Imbizo-CS {{ imbizo_version }}, confirm the dictionary versions above, and rerun the same report from the Reports menu. No external resources are required.</p>
</section>
```

All templates avoid external fonts, scripts, images, CDNs, and remote
validators. SVG charts are inline and must include `<title>` and `<desc>`.
