# Mixed-Code Varieties in Imbizo-CS v1.5

Imbizo-CS v1.5 adds mixed-code variety mode for projects that work with
Tsotsitaal, Iscamtho, Kaaps, Sabela, or related practices. This feature exists
because some multilingual speech cannot be honestly described as a neat switch
from Language A to Language B. But it also carries risk. Naming a variety can
recognize linguistic creativity and social history. It can also freeze a living
practice into a checklist, mislabel speakers, or reproduce stigma. This guide
explains how to use the mode carefully.

## Names Are Not Neutral

Tsotsitaal and Iscamtho are often discussed as urban South African mixed-code
practices connected to township histories, youth identities, multilingual
repertoires, and social positioning (Slabbert & Myers-Scotton, 1997; Hurst,
2008; Ntshangase, 2002). Kaaps has its own long history in the Western Cape, including ties to
Afrikaans, Malay, Khoisan, English, local religious and cultural life, and
struggles over respectability and standard language ideologies (McCormick, 2002;
Hendricks, 2016). Sabela is associated in available literature with prison and
criminal argot contexts, which makes it especially sensitive to annotate without
community and ethical care. South African sociolinguistic context matters for
all of these labels (Mesthrie, 2008).

These labels do not name fixed objects in the way a software list might imply.
They are historically situated, socially evaluated, and internally diverse.
Speakers may embrace, reject, joke with, avoid, or contest the labels. Some
researchers may prefer "mixed code," "urban youth register," "Kaaps Afrikaans,"
"township style," or a project-specific term. Others may reject variety labels
for a particular corpus. Imbizo-CS therefore makes mixed-code mode opt-in and
requires researcher confirmation before a span receives a variety label.

## Why Ordinary Code-Switching Labels May Fail

In a simple code-switching analysis, a researcher might ask: which language is
the Matrix Language, which is the Embedded Language, and where does the switch
occur? That can be useful for many utterances. But mixed-code varieties can
challenge the assumption that there are two separable systems visible on the
surface. Lexicon, morphology, discourse markers, pronunciation, stance, and
social identity may work together in ways that are not captured by a single
ML/EL label.

Slabbert and Myers-Scotton describe Tsotsitaal and Iscamtho as practices with
code-switching and in-group identity dimensions (Slabbert & Myers-Scotton,
1997). Hurst's work on Tsotsitaal highlights historical and social complexity
(Hurst, 2008). McCormick's discussion of language in Cape Town likewise shows
that Kaaps cannot be reduced to "non-standard Afrikaans" without losing the
social and political stakes of naming (McCormick, 2002). Imbizo-CS therefore
lets a span carry a mixed-code variety label in addition to token-level language
labels, memos, and ordinary annotations.

## What the Dictionaries Do

The mixed-code YAML dictionaries are not definitions of the varieties. They are
starter evidence profiles. Each profile may include signature vocabulary,
possible morphosyntactic notes, a social-context paragraph, and a required
`caveats` field. The caveats must appear in any report that draws on the variety
data. This is not decoration. It is a protection against turning a local,
historical, contested practice into a silent software category.

A dictionary entry can say that a word has been reported in scholarship or in
project-local review. It cannot say that a speaker "is Tsotsitaal" or that an
utterance "is Kaaps" by lexical evidence alone. The detector only measures
whether a contiguous span contains enough profile vocabulary to be worth the
researcher's attention. The GUI warning states this plainly: mixed-code
detection identifies lexical evidence only, and variety identification requires
speaker, setting, and broader sociolinguistic context.

This design is intentionally different from a conventional monolingual
dictionary. A monolingual dictionary often tries to list accepted words and
meanings for a language. A mixed-code profile in Imbizo-CS lists evidence that
may be relevant to a research question. It also records uncertainty, source,
review status, and caveats. The profile is therefore closer to a fieldwork memo
or coding aid than to an official lexicon. It should be copied into a project and
adapted only with clear notes about who made the change and why.
Treat every profile as situated evidence.

## Worked Examples

All examples below are fictional or paraphrased. They are not authoritative
samples of the named varieties.

Example 1 (# fictional example): A youth interview includes a short span with
several words that match the project-local Tsotsitaal profile. The detector
suggests a span and displays "lexical evidence only." The researcher checks the
speaker context, interview topic, and surrounding language before deciding
whether to accept the span, refine its boundaries, or reject it.

Example 2 (# fictional example): A Cape Town interview includes Afrikaans and
English forms, plus local words that a participant identifies as Kaaps. The
researcher may create a project-local Kaaps profile entry with a memo naming the
participant's own description. The report must reproduce the caveats and should
not treat the entry as proof that all similar forms in other projects are Kaaps.

Example 3 (# fictional example): A transcript includes vocabulary associated by
some sources with Sabela. The project is not about prison language and the
researcher lacks community review. The safest choice may be to leave mixed-code
mode disabled, or to mark the item as uncertain with `verified: false` and a
clear note. Stigmatizing labels should never be applied silently.

## Methodological Care

Mixed-code annotation asks the researcher to slow down. Before enabling the
feature, ask whether a named-variety label fits the project's epistemological
stance. Is the label used by participants? Is it used by the researcher? Is it
used in scholarship? Does it carry stigma? Does it flatten differences between
generation, neighborhood, race, class, school, religion, gender, or migration
history? Does the analysis need a named variety at all, or would a project-local
tag such as `urban register`, `peer talk`, or `participant term` be more honest?

When working with stigmatized varieties, use participant-preferred terminology
where possible. Avoid presenting dictionary matches as social identity claims.
Record uncertainty. Keep memos. Include caveats in reports. If community review
is available, invite reviewers to comment on dictionary entries, but do not make
one reviewer stand in for an entire community. Disagreement should be preserved,
not averaged away.

Researchers should also consider what not to annotate. If a term appears in an
interview about policing, schooling, gangs, prisons, religion, or migration, a
variety label may carry consequences beyond linguistic description. It can
attach stigma to a participant or make a community appear more homogeneous than
it is. In those cases, a neutral tag such as `locally salient term`, a memo, or
no variety label at all may be more ethical. The absence of a label is not a
failure of analysis when the label would exceed the evidence.

Students using the feature for a thesis should write a short positionality note.
That note can explain whether the researcher is a community member, an outside
analyst, a learner of the variety, or working through translators and reviewers.
The point is not to confess inadequacy. The point is to help readers understand
the conditions under which labels were assigned.

## Disabling Mixed-Code Detection

Mixed-code mode is off by default. To keep it off, leave the project setting
"Enable mixed-code variety analysis" unchecked. Existing token-level annotation,
MLF fields, triggers, metrics, and exports continue to work. If a project
imported from another machine already contains stored mixed-code spans, Imbizo-CS
shows them read-only until the researcher enables the mode. This prevents hidden
data loss while avoiding accidental endorsement of a framework the researcher
does not want to use.

If you enable mixed-code mode and later decide it does not fit, you can disable
new suggestions while keeping existing spans in the database for audit. Do not
delete them just to make the interface simpler. Instead, record in a project memo
that the mixed-code lens was considered and rejected or limited. That record can
be valuable for methods writing.

## Reporting Mixed-Code Findings

The Mixed-Code Variety Profile report counts accepted spans by variety, speaker,
and time range. It also prints the active dictionary's caveats verbatim. In a
thesis or article, report the evidence level. For example: "The project used an
opt-in mixed-code span tool to flag candidate Tsotsitaal-flavored lexical spans;
all accepted spans were manually reviewed, and the dictionary caveats were
included in the exported report" (Slabbert & Myers-Scotton, 1997; Hurst, 2008).

Do not write that the software "identified Tsotsitaal speakers" or "detected
Kaaps" unless the research design independently supports that claim. Imbizo-CS
does not certify identities. It helps keep evidence, uncertainty, and researcher
interpretation visible.

When comparing speakers or scenes, avoid ranking people by how much of a named
variety they "have." Counts of accepted spans are descriptive summaries of
annotated evidence, not measures of authenticity. A higher count may reflect a
topic, an interviewer's wording, a participant's comfort, a transcription
choice, or a dictionary bias. The report is most useful when it leads the
researcher back to the excerpts, not when it replaces them.

Finally, remember that a living variety changes faster than a shipped software
dictionary. v1.5 dictionaries start at version `0.1.0` precisely because they
are provisional. If your project develops better entries, preserve them in the
project folder and, where ethical, share them through the community review
workflow rather than treating them as private corrections.
