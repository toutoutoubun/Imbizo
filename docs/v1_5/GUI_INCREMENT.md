# v1.5 Deliverable 6 - GUI Increment

This document specifies the v1.5 GUI additions for sister-language
disambiguation, triggered-switching evidence, mixed-code variety spans,
phonological integration evidence, comparable interop exports, and offline
community review. All controls are advisory and opt-in. No interface element
may silently replace the researcher's annotation.

## 1. Annotation Editor - Updated Wireframe

```text
+--------------------------------------------------------------------------------+
| Menu: Project  Import  Annotate  Metrics  Reports  Review  Settings            |
| Toolbar: [Run LID] [Show Triggers] [Mixed-Code Span] [Send to Community Review] |
+--------------------------------------------------------------------------------+
| Waveform / timeline                                                             |
| [play] [pause] [zoom] [segment controls]                                        |
+--------------------------------------------------------------------------------+
| Transcript pane                                                                 |
|                                                                                |
|  S01  Ngithenge   i-laptop [zul/xho? v] [? Why]   entsha   izolo              |
|                  [Trigger: none v]                                             |
|                                                                                |
|  Drag selection mode: [Mixed-Code Span]  selected tokens -> [variety v] [Save]  |
+--------------------------------------+----------------------+------------------+
| Annotation grid                      | Phonological Evidence| Memo pane        |
| token | lang | ML | EL | 4-M | Trig | token: i-laptop      | Free memo text   |
| ...   | ...  | ...| ...| ... | none | [ ] vowel epenthesis | Tags             |
|       |      |    |    |     | trig | [ ] cluster simplify | Provenance       |
|       |      |    |    |     | ...  | [ ] tonal reassignment|                 |
|                                      | Note: [____________] |                  |
|                                      | [Apply to many]      |                  |
+--------------------------------------+----------------------+------------------+
| Status: v1.5 dictionaries active: sister_lang=0.1.0 triggers=0.1.0             |
+--------------------------------------------------------------------------------+
```

### New Controls

| Control | Placement | Default state | Empty / loading / error states | Shortcut | Accessibility | Color-blind-safe styling |
| --- | --- | --- | --- | --- | --- | --- |
| Sister-Language Disambiguator dropdown | Inline next to a token in transcript and mirrored in the language grid cell when `disambiguate_sister_languages` produced a tie verdict. | Hidden unless a token has a sister-language tie. If shown, value is `ambiguous` until accepted. | Empty: "No sister-language tie for this token." Loading: "Scoring local evidence..." Error: YAML diagnostic with file path and missing field. | `Alt+L` on focused token. | Screen-reader label: "Sister-language disambiguation for token {surface}". Tab order follows token, dropdown, Why link. | Use shape plus text, not color alone: striped amber outline for ambiguous, solid blue outline for accepted. |
| "Why this language?" evidence link | Immediately after sister-language dropdown. | Collapsed. | Empty: "No evidence matched." Loading: disabled with spinner text. Error: "Evidence could not be loaded." | `Alt+W` on focused token. | Button role, expanded/collapsed state announced. | Link has underline and icon marker, not color alone. |
| Trigger mini-toggle | Transcript token hover/focus overlay and grid `Trig` column. Values: `none`, `trigger`, `triggered`. | `none`; suggested values show `auto` badge until accepted or rejected. | Empty: no matched trigger candidate. Loading: "Scanning trigger window..." Error: dictionary diagnostic. | `Alt+T` cycles values; `Shift+Alt+T` opens menu. | Screen-reader label: "Trigger role for token {surface}". Tooltip text available on focus. | Use icons: circle for none, upward marker for trigger, right arrow marker for triggered; colors are secondary. |
| Mixed-Code Span selection tool | Toolbar button and transcript drag mode. | Off. When enabled, cursor changes to span-selection mode. | Empty: "Select two or more tokens to mark a span." Loading: "Checking variety evidence..." Error: profile YAML diagnostic. | `Alt+M` toggles span mode; `Esc` cancels selection. | Drag alternative: keyboard range selection with `Shift+Arrow`. Screen-reader announces selected token count. | Span underline uses double border and label chip, not color alone. |
| Variety dropdown for span | Appears near selected span after drag or keyboard selection. | No value selected. Stored candidate span shows suggested variety plus `auto` badge. | Empty: "No mixed-code varieties enabled for this project." Loading: disabled until profiles load. Error: profile parse error with path. | `Alt+V` opens variety dropdown. | Label: "Mixed-code variety for selected span". | Dropdown includes text labels and short variety codes. |
| Phonological Evidence sidebar | Right-side panel between annotation grid and memo pane, replacing noun-class panel when active token is class-tagged and non-host. | Closed by default; opens on eligible token focus or `Alt+P`. | Empty: "Select a class-tagged non-host token to record phonological evidence." Loading: "Loading phonology dictionary..." Error: YAML diagnostic. | `Alt+P` open/close; `Space` toggles focused checkbox. | Every checkbox has explicit feature label and dictionary source in accessible description. | Checkbox state plus text; no color-only status. |
| Send to Community Review | Annotation toolbar and new top-level Review pane. | Enabled when a project is open. | Empty: "No reviewable targets selected." Loading: "Creating review packet..." Error: packet write or signature diagnostic. | `Alt+R` opens review packet dialog. | Button label is explicit; confirmation dialog has focus trap. | Neutral high-contrast button, warning icon only for unsafe states. |

## 2. Sister-Language Disambiguator Detail

```text
+------------------------------------------------------+
| Sister-Language Evidence                             |
| Token: "ndi-hamba"                                   |
| Pair: zul <-> xho                                    |
+------------------------------------------------------+
| Ranked verdict                                       |
| 1. xho  confidence 0.72  [########------]            |
|    tags: morph_ndi_xho, context_ctx1_xho             |
| 2. zul  confidence 0.18  [###-------------]          |
|                                                      |
| [Accept xho] [Keep ambiguous] [Override...]          |
+------------------------------------------------------+
| Why? [expand]                                        |
| Source: Du Plessis & Visser (1992); Mesthrie (2002) |
| Evidence: ndi- matched first-person cue; nearby      |
| manually labelled xho token contributed weak context.|
+------------------------------------------------------+
```

Header shows token surface and candidate language pair. Body displays the
ranked `SisterLangVerdict`: language, confidence bar, evidence tags, and a
plain-language narrative. Footer has a "Why?" expandable panel that cites the
active YAML dictionary `source` field. Accepting a verdict updates the token
language and stores confidence/evidence. Keeping ambiguous is a valid outcome.

## 3. Trigger Highlighter - Behavior Spec

When a switch boundary is detected, the editor calls
`find_trigger_candidates(utterance_tokens, switch_index, window_left=3,
window_right=0)`. The preceding 1-3 tokens are scanned against local trigger
dictionaries. No remote checker, model, or cloud resource is used.

Candidates are highlighted with a dotted outline and a small `trigger?` badge.
Hover and keyboard focus show a tooltip with trigger type, matched dictionary
entry, confidence, distance from switch point, and note. Right-click or
keyboard menu opens:

```text
+-----------------------+
| Trigger suggestion    |
| Type: borrowing       |
| Entry: manager        |
| Confidence: 0.68      |
| [Confirm trigger]     |
| [Reject suggestion]   |
| [Add memo...]         |
+-----------------------+
```

Confirmed triggers persist to `trigger_links`, update token trigger roles, and
write a provenance event. Rejected suggestions remain visible in provenance but
do not affect metrics. Triggering is presented as a candidate context following
Clyne's typology, never as proof of speaker motivation (Clyne, 1967, 2003).

## 4. Mixed-Code Variety Mode - Behavior Spec

Project setting: "Enable mixed-code variety analysis" is off by default. When
disabled, no detector runs and no mixed-code badges are shown, except stored
legacy spans in read-only review mode.

```text
+------------------------------------------------------+
| Mixed-Code Variety Analysis                          |
| [x] Enabled for this project                         |
| Active profiles: tsotsitaal, kaaps                   |
+------------------------------------------------------+
| WARNING                                              |
| Mixed-code detection identifies lexical evidence     |
| only. Variety identification requires consideration  |
| of speaker, setting, and broader sociolinguistic     |
| context (Slabbert & Myers-Scotton, 1997; Hurst,      |
| 2008; McCormick, 2002).                              |
+------------------------------------------------------+
| Candidate spans                                      |
| tsotsitaal  conf 0.56  evidence 3  [auto]            |
| [Accept] [Refine] [Reject] [Memo]                    |
| kaaps       conf 0.43  evidence 2  [auto]            |
| [Accept] [Refine] [Reject] [Memo]                    |
+------------------------------------------------------+
```

For each detected span, the panel shows variety, confidence, evidence count,
matched forms, and actions: Accept, Refine, Reject. Refine opens span handles
so the researcher can adjust boundaries. Reject stores a reason if provided.
The warning banner text is mandatory, persistent, and translatable.

## 5. Phonological Evidence Sidebar - Detail

```text
+------------------------------------------------------+
| Phonological Evidence                                |
| Token: i-laptop                                      |
| Host frame: zul  Source stem: eng                    |
| Dictionary: phonology/zul.yaml v0.1.0                |
+------------------------------------------------------+
| Observed in this token?                              |
| [ ] vowel_epenthesis                                 |
|     Example: English school -> isiZulu isikole       |
| [ ] consonant_cluster_simplification                 |
| [ ] tonal_reassignment                               |
| [ ] stress_pattern_shift                             |
| [ ] click_reduction                                  |
|                                                      |
| Note                                                |
| [______________________________________________]     |
|                                                      |
| [Save evidence] [Apply feature to multiple tokens]   |
+------------------------------------------------------+
```

The sidebar opens only for a class-tagged non-host token. Feature rows come
from the active language's phonology dictionary. Each row shows feature type,
description, example, citation, `verified` status, and note. "Apply feature to
multiple tokens" opens a filterable token picker and requires confirmation
before bulk edit. Text-only projects may leave phonological fields unavailable;
missing evidence is not scored as negative evidence.

## 6. Metrics Dashboard - New Tabs

### Trigger Profile

Shows confirmed trigger counts by `trigger_type`, speaker, scene, and time
range. Suggested but unconfirmed triggers are excluded by default, with a
toggle "include suggestions" that changes the chart label visibly.

### Mixed-Code Distribution

Shows accepted span counts by variety and a timeline strip of spans. Each span
links back to the annotation editor. Rejected and pending spans are available
in a separate review table, not mixed into accepted metrics.

### Integration v2 Distribution

Shows a histogram of `phon_integration_score` values. If the v1.0 score is
present, the tab shows paired comparison: v1.0 morphology/concord score versus
v1.5 phonology-aware score. Tooltips list contributing factors and weights.

### Interop Preview

```text
+------------------------------------------------------------------+
| Interop Preview                                                   |
| [LIDES] [CHAT/CLAN]                                               |
|                                                                  |
| Preview text                                                     |
| # IMBIZO_LIDES 1.5                                                |
| TOK ...                                                          |
|                                                                  |
| Validation report                                                |
| [OK] Header present                                               |
| [WARN] Imbizo memos stored in sidecar                             |
| [LOSS] Round-trip not guaranteed for all v1.5 fields              |
|                                                                  |
| [Export LIDES] [Export CHAT/CLAN]                                 |
+------------------------------------------------------------------+
```

Validation is offline. The preview uses `to_lides`, `validate_lides`,
`to_chat`, and `validate_chat`. No external CHAT checker is contacted
(Barnett et al., 2000; MacWhinney, 2000).

## 7. Community Review Pane

```text
+--------------------------------------------------------------------------------+
| Community Review                                                               |
| [Outgoing] [Incoming]                                                          |
+--------------------------------------------------------------------------------+
| Outgoing                                                                       |
| packet id | created | targets | reviewer alias | status | [open folder]        |
| p-001     | today   | dict    | ReviewerA      | exported                    |
+--------------------------------------------------------------------------------+
| Incoming                                                                       |
| packet id | reviewer | signature | status      | action                      |
| p-002     | RevB     | verified  | pending     | [View diff] [Apply]        |
| p-003     | RevC     | failed    | pending     | [View diff] [Reject]       |
+--------------------------------------------------------------------------------+
| Diff viewer                                                                    |
| - old dictionary entry                                                         |
| + proposed dictionary entry                                                    |
| Mandatory comment: [________________________________________]                  |
| [Apply] [Reject] [Defer]                                                       |
+--------------------------------------------------------------------------------+
```

Outgoing lists review packets created from the current project. Incoming lists
received packets with status: pending, accepted, rejected, superseded. Each
incoming item shows a human-readable diff and signature verification result.
Apply, Reject, and Defer require a comment field. Auto-apply is never the
default and must be explicitly confirmed. Application writes provenance.

## 8. Empty / Error / Loading States

| Screen / control | No dictionary registered | YAML failed to load | Mixed-code disabled with stored span | Signature does not verify |
| --- | --- | --- | --- | --- |
| Sister-Language Disambiguator | "No sister-language dictionary registered for this pair." Provide Settings link. | Show file path, line/field if available, and "Suggestion unavailable; manual annotation still works." | Not applicable. | Not applicable. |
| Trigger Highlighter | "No trigger dictionary registered for this language." Trigger toggle remains manual. | Show diagnostic; disable suggestions but keep manual trigger role menu. | Not applicable. | Not applicable. |
| Mixed-Code Panel | "No mixed-code profiles enabled." Span tool remains manual only. | Show diagnostic and keep existing accepted spans visible. | Show read-only banner: "Mixed-code mode is off, but this project contains stored spans. Enable mode to edit them." | Not applicable. |
| Phonological Sidebar | "No phonology dictionary registered for this language." Free-text note remains available. | Show diagnostic; checkboxes disabled. | Not applicable. | Not applicable. |
| Interop Preview | Not applicable. | Not applicable unless sidecar source fails, then show validation error. | Stored spans are exported only if the researcher confirms inclusion. | Not applicable. |
| Community Review Pane | Not applicable. | Packet manifest parse error shown in incoming item. | Not applicable. | Mark packet as "signature failed"; disable Apply until researcher explicitly chooses "Import as untrusted pending review" with comment. |

Loading states must be text-visible and screen-reader-announced. Errors must be
plain-language and must not silently fall back to empty suggestions.

## 9. Internationalization

All new user-facing strings must be externalized to the i18n catalog. No
English string should be hardcoded in widget code. The mixed-code warning
banner is explicitly translatable.

New strings:

- "Sister-Language Disambiguator"
- "Why this language?"
- "No sister-language tie for this token."
- "Scoring local evidence..."
- "No evidence matched."
- "Keep ambiguous"
- "Override..."
- "Trigger"
- "none"
- "trigger"
- "triggered"
- "Scanning trigger window..."
- "Confirm trigger"
- "Reject suggestion"
- "Add memo..."
- "Mixed-Code Span"
- "Enable mixed-code variety analysis"
- "No mixed-code varieties enabled for this project."
- "Select two or more tokens to mark a span."
- "Checking variety evidence..."
- "Accept"
- "Refine"
- "Reject"
- "Mixed-code detection identifies lexical evidence only. Variety identification requires consideration of speaker, setting, and broader sociolinguistic context (Slabbert & Myers-Scotton, 1997; Hurst, 2008; McCormick, 2002)."
- "Phonological Evidence"
- "Select a class-tagged non-host token to record phonological evidence."
- "Loading phonology dictionary..."
- "Observed in this token?"
- "Apply feature to multiple tokens"
- "Save evidence"
- "Trigger profile"
- "Mixed-code distribution"
- "Integration v2 distribution"
- "Interop preview"
- "Export LIDES"
- "Export CHAT/CLAN"
- "Validation report"
- "Round-trip not guaranteed for all v1.5 fields"
- "Community Review"
- "Outgoing"
- "Incoming"
- "View diff"
- "Apply"
- "Reject"
- "Defer"
- "Mandatory comment"
- "Signature verified"
- "Signature failed"
- "Import as untrusted pending review"
- "Suggestion unavailable; manual annotation still works."
- "Mixed-code mode is off, but this project contains stored spans. Enable mode to edit them."
