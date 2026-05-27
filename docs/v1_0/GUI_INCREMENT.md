# v1.0 Deliverable 6 — GUI Increment

This document specifies GUI affordances for v1.0 A1 Noun-Class Engine, A2
Concord Agreement Tracker, and B1 4-M Model Annotation Layer. It does not add
backend features beyond Deliverable 5 and does not require internet access.

## 1. Annotation Editor — Updated Wireframe

```text
+--------------------------------------------------------------------------------+
| Menu / Project toolbar                                                          |
+--------------------------------------------------------------------------------+
| Waveform pane (MVP)                                                             |
| [play] [pause] [segment navigation]                                             |
+--------------------------------------------------------------------------------+
| Transcript pane (MVP)                                  | Noun Class [NEW] | Memo |
|                                                        | (collapsible)    | pane |
|  Speaker A: Ngithenge i-laptop entsha izolo.           |                  | MVP  |
|             ^ selected token                            |                  |      |
+--------------------------------------------------------------------------------+
| Annotation grid toolbar                                                        |
| [filter] [search] [bulk edit] [Show concord candidates] [NEW]                  |
+--------------------------------------------------------------------------------+
| Annotation grid (MVP + v1.0 columns)                                            |
| Token | Lang | Matrix | Embedded | 4-M [NEW] | Switch | Status | Memo | Auto    |
| i-laptop | eng | zul | eng | content v | intra | insertion | ... | auto/manual |
+--------------------------------------------------------------------------------+
| Status bar: Project saved | Dict: NC zul 0.1.0 / Concord zul 0.1.0 / 4-M eng 0.1.0 [NEW] |
+--------------------------------------------------------------------------------+
```

### New Control Placement And States

| Control | Placement | Default state | Empty state | Loading state | Error state | Shortcut | Accessibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Noun Class side panel | Right side, between transcript pane and memo pane | Collapsed unless a token with a supported Bantu language tag is selected | “Select a token inside a Bantu-tagged span to see class suggestions.” | “Loading local dictionary…” with progress text only | “Dictionary could not be read. Check project settings.” | `Ctrl+Alt+N` | Screen-reader label: “Noun class suggestions”; tab order after transcript token list and before memo pane; colors use blue/amber with icon labels. |
| Show concord candidates button | Annotation grid toolbar, after bulk edit | Disabled until a class-tagged head token is selected | Disabled with tooltip “Select a token with a noun class first.” | Button text: “Finding candidates…” | Inline banner in grid: “Concord candidates could not be loaded.” | `Ctrl+Alt+C` | Screen-reader label: “Show concord candidates for selected noun”; highlight also uses border style, not color alone. |
| 4-M dropdown column | Annotation grid, immediately right of Matrix/Embedded columns | `unassigned` | `unassigned` for all rows | Per-row spinner only if local YAML examples are loading | Dropdown remains editable; tooltip says “4-M examples unavailable.” | `Alt+4` when grid cell focused | Screen-reader label: “4-M morpheme type”; options announced with short explanations. |
| Dictionary version status indicator | Status bar, right side | Shows active dictionary versions or “Dictionaries off” | “No dictionary registered for selected language.” | “Checking local dictionaries…” | “Dictionary error: open Project Settings.” | `Ctrl+Alt+D` focuses status details | Text labels plus neutral icons; no red/green-only status coding. |

## 2. Noun Class Side Panel — Detail

```text
+--------------------------------------+
| Noun Class                           |
| Token: i-laptop     Language: eng    |
+--------------------------------------+
| Candidates from local dictionary     |
|                                      |
| #9   prefix: i-     domain: objects  |
|      [Accept] [Override]             |
|                                      |
| #5   prefix: i-     domain: varied   |
|      [Accept] [Override]             |
|                                      |
| #1a  prefix: u-     domain: names    |
|      [Accept] [Override]             |
+--------------------------------------+
| Why this class? >                    |
+--------------------------------------+
```

Header: the selected token surface and current language tag. If the token is in
an English-tagged loan inside a Bantu-tagged span, the panel still shows the
token but marks the suggestion context as “loanword review.”

Body: ranked candidates from `suggest_class(token_surface, prefix_guess,
language_code)`. Each row shows class number, matched prefix, semantic domain,
verification status, and `verified: false` note where present. “Accept” writes
the selected class to the token. “Override” opens a small form for class number,
prefix, source note, and reviewer confidence.

Footer: “Why this class?” expands to show the dictionary `source`, candidate
prefix match, verification note, and a reminder that suggestions are advisory
(Poulos & Msimang, 1998; Du Plessis & Visser, 1992; Demuth, 2000).

Empty state: “Select a token inside a Bantu-tagged span to see class
suggestions.”

## 3. Concord Highlighter — Behavior Spec

When the researcher clicks “Show concord candidates” with a class-tagged head
noun selected, the UI calls `find_concord_candidates(utterance_tokens,
head_token_index, head_class, language_code)`.

Behavior:

- Candidate tokens in the same utterance receive a color-blind-safe amber
  outline and a dotted underline. The selected head noun receives a blue outline.
- Hover tooltip shows: concord type (`SC`, `OC`, `AC`, `PC`, `RC`, `DEM`),
  noun class, matched marker, confidence, and dictionary verification note.
- Clicking a candidate opens a mini-dialog:

```text
+----------------------------------+
| Confirm concord candidate        |
| Head: i-laptop  Class: 9         |
| Candidate: entsha                |
| Type: AC  Confidence: 0.82       |
| [Confirm] [Reject] [Uncertain]   |
+----------------------------------+
```

- Confirm persists a `concord_links` row with `agreement_status=confirmed`.
- Reject persists the row with `agreement_status=mismatch` only if the
  researcher chooses “Keep rejected evidence”; otherwise it is dismissed without
  storage.
- Uncertain persists `agreement_status=uncertain`.
- Every persisted decision writes a provenance event with token IDs, concord
  type, class, dictionary version, and reviewer action.

This highlighter supports analysis of agreement evidence, but does not infer
Matrix Language automatically (Myers-Scotton, 1993; Myers-Scotton, 2002).

## 4. 4-M Dropdown — Behavior Spec

Values:

- `content`
- `early_system`
- `bridge_late_system`
- `outsider_late_system`
- `unassigned`

The dropdown sits directly to the right of Matrix/Embedded language columns.
Changing a value stores the token’s 4-M type and source. If the value came from
`suggest_four_m_type`, the cell displays a small `auto` badge until the
researcher accepts, changes, or clears it.

Hover behavior:

- Shows examples from the active language’s 4-M YAML.
- Shows `type_justification` and `source`.
- Shows `verified: false` notes prominently.

The dropdown is optional and theory-aware, not theory-enforcing. It supports
the System Morpheme Principle while allowing researchers to leave the field
blank or use non-MLF interpretations (Myers-Scotton, 1993; Myers-Scotton, 2002;
Jake, Myers-Scotton & Gross, 2002; Muysken, 2000).

## 5. Metrics Dashboard — New “MLF Audit” Tab

```text
+--------------------------------------------------------------------------------+
| Metrics Dashboard                                                               |
| [Language proportions] [Switching] [Concord] [MLF audit] [NEW]                 |
+--------------------------------------------------------------------------------+
| Filters: Speaker [all v] Scene [all v] Time [00:00 - 01:00] [Apply]            |
+--------------------------------------------------------------------------------+
| Utterance verdicts                                                              |
| Time      Speaker  Verdict             Review?  System morphemes  Concord      |
| 00:01:12  S1       consistent          no       3                 2/2          |
| 00:02:44  S2       mixed               yes      4                 1/3          |
| 00:03:10  S1       insufficient_data   yes      0                 0/0          |
+--------------------------------------------------------------------------------+
| Drill-down                                                                      |
| Token      Language   4-M type                Evidence note                    |
| u-         zul        outsider_late_system    system morpheme                  |
| i-laptop   eng        content                 switched content candidate       |
+--------------------------------------------------------------------------------+
| [Export CSV]       [How is this computed?]                                      |
+--------------------------------------------------------------------------------+
```

Behavior:

- Per-utterance verdicts come from `check_mlf_compatibility`: `consistent`,
  `mixed`, or `insufficient_data`.
- Selecting a row opens the evidence drill-down: token ID, surface, language,
  4-M type, and narrative explanation.
- Filters apply locally over already-loaded project data: speaker, scene, and
  time range.
- Export-to-CSV writes a local file only.
- “How is this computed?” opens a plain-language local help panel explaining
  the System Morpheme Principle and the advisory nature of the checker
  (Myers-Scotton, 1993; Myers-Scotton, 2002; Jake, Myers-Scotton & Gross,
  2002).

## 6. Empty / Error / Loading States

| Condition | Annotation editor | Noun Class panel | Concord highlighter | 4-M dropdown | MLF audit tab |
| --- | --- | --- | --- | --- | --- |
| No project loaded | Existing MVP empty project screen; v1.0 controls disabled | Hidden | Button disabled | Column hidden or disabled | “Open a project to view MLF audit.” |
| Active language has no dictionary registered | Status bar: “No dictionary for selected language.” | “No noun-class dictionary registered for this language.” | “No concord dictionary registered for this language.” | Tooltip: “No 4-M dictionary registered.” | Rows still shown if manual tags exist; otherwise dictionary notice. |
| Dictionary YAML failed to parse | Non-modal error banner with “Open Project Settings” | “Dictionary could not be read.” | “Concord dictionary could not be read.” | Dropdown editable, examples unavailable | “Dictionary examples unavailable; audits use existing manual tags only.” |
| Token has no class tag yet | Grid row shows blank noun-class state | Shows candidates if possible; otherwise empty prompt | Button disabled with tooltip “Assign or accept a noun class first.” | Unaffected | Audit uses 4-M tags only and marks concord evidence as 0/0. |
| No 4-M tags annotated yet | 4-M column shows `unassigned` | Unaffected | Concord still works if class tags exist | Cells show `unassigned` | “No 4-M tags yet. Annotate tokens to run MLF audit.” |

All loading states must be text-first and must not rely on animation. This keeps
the UI usable on low-resource hardware and screen readers.

## 7. Internationalization

All new user-facing strings must be externalized in the i18n catalog. No widget
code may hardcode English text.

New strings:

- `noun_class.panel.title`: “Noun Class”
- `noun_class.panel.empty`: “Select a token inside a Bantu-tagged span to see class suggestions.”
- `noun_class.panel.loading`: “Loading local dictionary…”
- `noun_class.panel.error`: “Dictionary could not be read. Check project settings.”
- `noun_class.header.token`: “Token”
- `noun_class.header.language`: “Language”
- `noun_class.candidates.title`: “Candidates from local dictionary”
- `noun_class.action.accept`: “Accept”
- `noun_class.action.override`: “Override”
- `noun_class.explain.title`: “Why this class?”
- `noun_class.loanword_context`: “loanword review”
- `concord.toolbar.show_candidates`: “Show concord candidates”
- `concord.toolbar.disabled_no_class`: “Select a token with a noun class first.”
- `concord.loading`: “Finding candidates…”
- `concord.error`: “Concord candidates could not be loaded.”
- `concord.dialog.title`: “Confirm concord candidate”
- `concord.dialog.confirm`: “Confirm”
- `concord.dialog.reject`: “Reject”
- `concord.dialog.uncertain`: “Uncertain”
- `concord.tooltip.type`: “Concord type”
- `concord.tooltip.class`: “Class”
- `concord.tooltip.confidence`: “Confidence”
- `four_m.column.title`: “4-M”
- `four_m.value.content`: “content”
- `four_m.value.early_system`: “early_system”
- `four_m.value.bridge_late_system`: “bridge_late_system”
- `four_m.value.outsider_late_system`: “outsider_late_system”
- `four_m.value.unassigned`: “unassigned”
- `four_m.badge.auto`: “auto”
- `four_m.tooltip.examples_unavailable`: “4-M examples unavailable.”
- `status.dictionaries.off`: “Dictionaries off”
- `status.dictionaries.no_language`: “No dictionary registered for selected language.”
- `status.dictionaries.checking`: “Checking local dictionaries…”
- `status.dictionaries.error`: “Dictionary error: open Project Settings.”
- `metrics.tab.mlf_audit`: “MLF audit”
- `metrics.mlf.no_project`: “Open a project to view MLF audit.”
- `metrics.mlf.no_tags`: “No 4-M tags yet. Annotate tokens to run MLF audit.”
- `metrics.mlf.export_csv`: “Export CSV”
- `metrics.mlf.how_computed`: “How is this computed?”
- `metrics.mlf.verdict.consistent`: “consistent”
- `metrics.mlf.verdict.mixed`: “mixed”
- `metrics.mlf.verdict.insufficient_data`: “insufficient_data”
- `metrics.mlf.filter.speaker`: “Speaker”
- `metrics.mlf.filter.scene`: “Scene”
- `metrics.mlf.filter.time_range`: “Time range”
- `metrics.mlf.filter.apply`: “Apply”

