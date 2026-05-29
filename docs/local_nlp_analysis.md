# Local NLP analysis pipeline

Imbizo-CS Workbench now has one shared local analysis pipeline for the GUI and
the command line. The pipeline is intentionally conservative: it connects local
tools that already exist in the project, records what each stage did, and leaves
interpretation with the researcher.

The pipeline runs fully offline. It does not call a server, send telemetry, or
download a model. If an optional model such as `models/lid/lid.176.ftz` is
present, Local LID can use it; otherwise the project falls back to the bundled
low-resource heuristic detector and records that choice in the run report.

## Stages

1. **Local LID**: applies advisory automatic language labels while preserving
   manual labels.
2. **Switch profile**: counts adjacent language transitions and stores a sample
   of switch points.
3. **Noun-class hints**: proposes local prefix-based noun-class candidates for
   isiZulu, isiXhosa, Sesotho, and Setswana where dictionaries are available.
4. **Trigger candidates**: flags Clyne-style trigger contexts as evidence
   prompts, not causal explanations (Clyne, 1967, 2003).
5. **Mixed-code candidates**: opt-in only; detects lexical evidence from local
   mixed-code dictionaries without declaring a speaker, text, or community
   practice as Tsotsitaal, Iscamtho, Kaaps, or Sabela.
6. **Metrics**: stores language proportions, switch count, switch density,
   M-index, I-index, burstiness, trigger co-occurrence, and optional KWIC rows.

Each run writes a JSON report under:

```text
<project>/logs/analysis/local_nlp_analysis_<run-id>.json
```

It also writes a provenance event into the local SQLite database. This makes the
analysis citable and repeatable: a researcher can state which Imbizo-CS version
produced the numbers and which stages were enabled.

## GUI

Open a project, go to **Metrics**, and press **Run full local NLP analysis**.
The table shows the persisted metrics, while the JSON report contains the
stage-by-stage evidence trail.

## CLI

For reproducible headless work:

```bash
imbizo-cs analyze --project /path/to/project
```

Useful variants:

```bash
imbizo-cs analyze --project /path/to/project --skip-lid
imbizo-cs analyze --project /path/to/project --include-mixed-code
imbizo-cs analyze --project /path/to/project --json
```

## Limitations

The pipeline is a foundation, not a claim of finished linguistic authority.
Local LID is only as strong as the installed local resources. Noun-class and
trigger stages are advisory. Mixed-code detection is deliberately opt-in and
never identifies a speaker or text without researcher judgement. These
limitations are part of the design: automation supports humanities analysis; it
does not replace it.
