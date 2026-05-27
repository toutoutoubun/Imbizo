# v1.0 Deliverable 1 — Increment Overview

## 1. Plain-Language Summary

The MVP of Imbizo-CS Workbench helped researchers keep multilingual interview data local, annotate language choices token by token, and calculate reproducible code-switching metrics. Version 1.0 does not replace that work. It adds three opt-in layers for researchers who need to look more closely at how South African languages work inside mixed utterances: noun classes, concord agreement, and the 4-M model of morphemes.

For many Bantu languages, nouns are not isolated words that simply carry meaning by themselves. A noun belongs to a class, and that class often shapes agreement elsewhere in the phrase or clause: prefixes, pronouns, adjectives, demonstratives, verbs, and other linked forms may echo the class of the noun (Demuth, 2000; Poulos & Msimang, 1998). In code-switching analysis, this matters because a switch is not only a change from one language label to another. A researcher may want to know whether an English noun is being pulled into an isiZulu agreement frame, whether a Setswana concord remains stable around an inserted English word, or whether mixed forms show local urban varieties behaving differently from classroom or interview norms (Slabbert & Myers-Scotton, 1997).

The new Noun-Class Engine helps the researcher record possible noun-class information without pretending the software can settle the analysis. Suggestions are local, editable, and marked as suggestions. Unverified dictionary entries remain explicitly unverified. The Concord Agreement Tracker then lets the researcher inspect whether agreement relations appear to hold, shift, or break across a code-switched stretch. This gives a more precise view of structure than counting languages alone, because agreement can show how a mixed utterance is being organized grammatically (Demuth, 2000; Poulos & Msimang, 1998).

The third addition, the 4-M Model Annotation Layer, gives researchers a way to distinguish different kinds of morphemes in mixed speech. Myers-Scotton’s 4-M model separates content morphemes from several kinds of system morphemes, which can help explain why some parts of an utterance are easier to switch than others (Myers-Scotton, 1993; Myers-Scotton, 2002). In the MVP, Matrix Language and Embedded Language labels could show that a switch happened. In v1.0, a researcher can ask what kind of grammatical material is involved in that switch. Is the switch centered on a content noun, a system morpheme, or a larger alternational stretch? That distinction can sharpen comparison with insertional, alternational, or constraint-based accounts of code-mixing (Muysken, 2000; Poplack, 1980).

The new research questions are more grammatical and more interpretive. Which noun classes are most often involved when English nouns enter isiZulu or isiXhosa stretches? Do concord patterns remain in the local African language when English lexical material appears? Are system morphemes more resistant to switching than content morphemes in a particular speaker, scene, or register? Do Tsotsitaal, Iscamtho, Kaaps, or other user-defined varieties pattern differently from standard-language expectations (Slabbert & Myers-Scotton, 1997)? Version 1.0 therefore moves beyond “which languages are present?” toward “how are languages and morphemes working together in this particular interaction?” The researcher remains the final interpreter throughout.

## 2. ASCII Architecture Diagram

```text
                         Researcher
                             |
                             v
                    gui.annotation_editor
                       |        |        |
                       |        |        +--[v1.0 NEW]--> B1 FourM Layer
                       |        +-----------[v1.0 NEW]--> A2 Concord Tracker
                       +--------------------[v1.0 NEW]--> A1 NounClass Engine
                             |
                             v
                       core.annotation
                       |      |      |
                       |      |      +--[v1.0 NEW]--> four_m_tags
                       |      +---------[v1.0 NEW]--> concord_relations
                       +----------------[v1.0 NEW]--> noun_class_annotations
                             |
                             v
                       core.morphology
                       |      |      |
                       |      |      +--[v1.0 NEW]--> B1 FourM suggestions
                       |      +---------[v1.0 NEW]--> A2 concord candidates
                       +----------------[v1.0 NEW]--> A1 noun-class dictionaries
                             |
                             v
+----------------+     core.metrics      +-----------------------+
| MVP importers  |--------|-------------->| gui.metrics_dashboard |
| EAF/TextGrid/  |        |               +-----------------------+
| tabular/audio  |        |
+----------------+        +--[v1.0 NEW]--> noun-class distributions
                          +--[v1.0 NEW]--> concord-pattern summaries
                          +--[v1.0 NEW]--> 4-M morpheme summaries
                             |
                             v
                       core.export
                       |      |
                       |      +--[v1.0 NEW]--> CSV/XLSX/JSON fields for A1/A2/B1
                       +-----------> EAF/TextGrid/HTML/PDF MVP exports
                             |
                             v
                       core.provenance
                       |      |
                       |      +--[v1.0 NEW]--> suggestion, override, and metric audit events
                       +-----------> MVP import/LID/annotation/export audit events

                       plugins.api
                       |      |
                       |      +--[v1.0 NEW]--> optional local dictionaries/analyzers
                       +-----------> MVP optional ASR/LID/export plugin boundary
```

## 3. Risk Register

| Risk | Affected Principle | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| Dictionary errors propagating into analysis | Humanities-led authority; reproducibility | Medium | High | Mark every dictionary-derived label as a suggestion, store `verified: false` for unverified entries, and log provenance for each accepted or overridden suggestion. |
| Researcher over-trust in automatic suggestions | Automation is auxiliary | Medium | High | Use visual “suggested” styling, require one-click acceptance or editing, and keep manual labels authoritative over all automatic output. |
| Migration corrupting MVP projects | Backward compatibility; data sovereignty | Low | High | Add only NULL-able columns/tables, run migrations inside SQLite transactions, create local backups before migration, and test against MVP sample projects. |
| New features bloating CPU/RAM usage on minimum hardware | Low-resource by design | Medium | Medium | Keep dictionaries lazy-loaded per project, avoid background model loading, cache small lookup tables, and allow A1/A2/B1 to stay disabled. |
| 4-M tags becoming a theoretical straitjacket for non-MLF traditions | Researcher interpretive authority; linguistic dignity | Medium | Medium | Make 4-M fields optional, allow blank/custom values, and document compatibility with Muysken and Poplack-style analyses rather than enforcing one theory (Muysken, 2000; Poplack, 1980). |
| Bantu morphology assumptions failing on Tsotsitaal / Iscamtho / Kaaps | Linguistic dignity; decolonial computing posture | High | High | Treat standard-language morphology as one resource, not a rulebook; allow user-defined varieties, local notes, rejected suggestions, and community-reviewed dictionaries (Slabbert & Myers-Scotton, 1997). |
| Concord categories being interpreted as proof of Matrix Language | Humanities-led authority | Medium | Medium | Present concord evidence as descriptive support only, not automatic theoretical conclusion, because Matrix Language analysis still requires researcher judgement (Myers-Scotton, 1993; Myers-Scotton, 2002). |
| Exported noun-class or 4-M fields being read without provenance context | Citable and reproducible | Low | Medium | Include provenance IDs, suggestion status, verification flags, and citation notes in CSV/XLSX/JSON/HTML exports. |

