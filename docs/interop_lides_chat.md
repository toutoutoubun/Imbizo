# LIDES and CHAT/CLAN Interoperability in Imbizo-CS v1.5

Imbizo-CS is built for local humanities research, but local work should not be
isolated. v1.5 adds export paths for LIDES and CHAT/CLAN so that South African
code-switching projects can travel into wider comparative conversations without
requiring cloud services or proprietary platforms (Barnett et al., 2000;
MacWhinney, 2000).

## Why Interoperability Matters

Researchers often need to compare findings across corpora, submit extracts to a
supervisor, share a dataset with a collaborator, or archive material in a format
that another tool can read. If Imbizo-CS only exported its own JSON, it would
protect local detail but make external comparison harder. If it only exported a
standard format, it would lose the special evidence needed for noun class,
concord, 4-M tags, triggers, mixed-code spans, and integration scores. v1.5 takes
a middle path: export the standard format, and write a companion sidecar or
validation report that documents what was preserved and what was lost.

## What LIDES Is

LIDES is a coding framework developed for language interaction data and
code-switching annotation (Barnett et al., 2000). It gives the international
code-switching community a shared way to represent language labels, switches,
and related coding decisions. Imbizo-CS maps token language, switch information,
and selected annotation fields into a LIDES-oriented text export. Because LIDES
does not natively carry every Imbizo-CS v1.0 and v1.5 field, the exporter also
records documented losses.

For example, a basic language label can usually be represented. A project-local
mixed-code caveat, a community-review status, or a phonological feature with a
long memo may require an Imbizo sidecar field. The validation report tells you
which fields were converted directly, which were represented approximately, and
which require the sidecar.

## What CHAT/CLAN Is

CHAT is the transcript format used by the CHILDES and TalkBank ecosystem, and
CLAN is the associated analysis suite (MacWhinney, 2000). CHAT has a structured
header, speaker tiers, and dependent tiers for annotations. Imbizo-CS exports
speaker lines, timestamps where possible, and dependent tiers for selected
metadata. The exporter runs only local checks. It does not contact a remote CHAT
validator.

CHAT/CLAN export is useful when a collaborator already works in that ecosystem
or when a project wants to align with broader transcript-analysis conventions.
It is not a perfect round-trip path back into full Imbizo-CS. Some v1.5 fields
need sidecar documentation.

For both export families, the guiding principle is reproducible loss. If a field
cannot be represented, the exporter should say so plainly. A silent loss is worse
than an incomplete export, because it lets a later analyst believe that the
standard file contains the full project.

## What Is Preserved

The exporters aim to preserve the core transcript text, speaker IDs, utterance
order, timestamps, language labels, and manually reviewed switch annotations.
Where possible, they also preserve token IDs through sidecar references. This is
important because exported files should remain citable and traceable. If a
published example comes from token `tok_004_02`, the researcher should be able
to return to the Imbizo project and inspect the original context.

v1.5 fields such as trigger links, mixed-code span labels, phonological features,
and integration v2 scores are exported in companion artifacts when the target
format lacks a native representation. The goal is honesty, not false
completeness.

## What May Be Lost

LIDES and CHAT/CLAN do not model every Imbizo-CS concept. Possible losses
include project-local dictionary caveats, community-review histories, detailed
formula weights, some provenance events, long free-text memos, and visual UI
states such as rejected suggestions. The validation reports list these losses in
plain language.

Do not hide losses in methods writing. A good methods section might say:
"Imbizo-CS annotations were exported to CHAT for transcript exchange. Token
language labels and speaker tiers were preserved; v1.5 mixed-code caveats,
review-packet history, and integration-score weights were retained in the
Imbizo sidecar and validation report" (MacWhinney, 2000).

The validation report is meant for both technical and non-technical readers. It
should list exported files, preserved fields, approximate mappings, lost fields,
and recommended citation language. If a supervisor or collaborator only opens
the standard LIDES or CHAT file, the report still gives the original researcher
a defensible record of what happened during conversion.

## Round-Tripping

Round-tripping means exporting data, using it elsewhere, then bringing it back.
Imbizo-CS supports cautious round-trip workflows, but full fidelity is not
guaranteed. Before exporting, create a project zip. After importing or comparing
an external file, inspect the validation report. If a field cannot round-trip,
record that in the project memo and methods notes.

For collaborative work, share the project zip when possible and use LIDES or
CHAT/CLAN as additional exchange formats. This keeps the richest local evidence
available while still supporting international comparison.

If a collaborator edits the exported file and sends it back, import it into a
copy of the project first. Compare the validation report against the original
export. Then decide whether to merge the changed transcript text, keep only
comments, or treat the returned file as a separate derivative dataset. This
extra caution protects the original local annotations.
