# Sister-Language Disambiguation in Imbizo-CS v1.5

This guide explains the v1.5 sister-language disambiguator for researchers who
already understand why language labels matter but do not want the software to
pretend that every token has an obvious answer. In South African interview data,
isiZulu and isiXhosa, or Sesotho and Setswana, can be close enough in form that
automatic language identification becomes uncertain. That uncertainty is not a
bug to hide. It is often part of the linguistic and social reality of the data.

## Close Languages, Distinct Histories

isiZulu and isiXhosa are both Nguni languages, with related noun-class systems,
overlapping grammatical patterns, and many cognate forms. Reference grammars show
structural similarities, but they also document distinctive phonological,
orthographic, lexical, and morphological patterns that matter in actual analysis
(Poulos & Msimang, 1998; Du Plessis & Visser, 1992). Sesotho and Setswana are
likewise closely related Sotho-Tswana languages. They share many broad Bantu
features, but they are not interchangeable labels. Cole's grammar of Setswana,
Lombard's work on Northern Sotho, and Mojapelo's study of definiteness all
remind us that grammatical closeness does not erase language-specific systems or
speaker identities (Cole, 1955; Lombard, 1985; Mojapelo, 2007).

For humanities research, the distinction is never only technical. A speaker may
move through family, school, church, work, migration, media, or political
histories that make one language label socially meaningful in a way another is
not. South African sociolinguistics has repeatedly shown that language choices
are bound up with region, race, class, schooling, institutional histories, and
post-apartheid identity work (Mesthrie, 2002, 2008). A token that looks
ambiguous to software may be quite clear to a participant, or it may be
deliberately ambiguous in context. Imbizo-CS therefore treats disambiguation as
an evidence panel, not as a final judgement.

## Why Automatic LID Gets Confused

Most lightweight language identification works by comparing a short text against
patterns learned from larger samples. That works reasonably for long stretches
of English or Afrikaans. It becomes fragile when the item is a short token,
proper name, borrowed word, agreement marker, discourse marker, or shared Bantu
form. The shorter the unit, the less evidence the classifier has. A one-syllable
form may be common in more than one language. A code-switched utterance may give
conflicting context. Non-standard spelling, hesitation, repetition, and
interview transcription conventions make the problem harder.

v1.5 responds by adding a rule-based disambiguator for selected sister-language
pairs. It does not use machine learning. It looks for transparent, local
evidence from YAML dictionaries: distinctive morphemes, distinctive lexemes,
orthographic features, phonotactic cues, and immediate utterance context. A
match might be an isiXhosa click letter in an otherwise ambiguous Nguni token,
a lexical cue documented in a grammar, or a neighboring token already confirmed
by the researcher. The result is a ranked suggestion with a confidence score and
evidence tags. The researcher can accept it, override it, or leave the token
ambiguous.

The disambiguator is intentionally conservative. It is better to preserve an
ambiguous label than to impose a confident but wrong label. That stance follows
the broader design of Imbizo-CS: automatic decisions are auxiliary, data remains
local, and community knowledge can revise shipped dictionaries.

This is also why the panel stores evidence codes rather than only a final label.
Evidence codes let a later reader see whether the suggestion came from spelling,
morphology, lexicon, or context. Two projects may reasonably weigh the same cue
differently, especially when speakers draw on regional or family repertoires.

## Worked Examples

The following examples are invented for training and interface explanation. They
are not claims about actual community usage. Treat them as "# fictional example"
unless you verify comparable forms against a reference grammar and your own
field context.

Example 1 (# fictional example): A transcript contains the token `ndiyabona` in
an utterance otherwise tagged as Nguni. The active `zul_vs_xho` dictionary
matches `ndi-` as a possible isiXhosa first-person subject marker. The side
panel shows a higher isiXhosa score, cites the dictionary source, and lists an
evidence tag such as `morph_ndi_xho`. The researcher may accept isiXhosa,
override to isiZulu if the participant's context supports that, or leave the
token as ambiguous.

Example 2 (# fictional example): A participant says a form transcribed as
`ngiyabona`. The dictionary marks `ngi-` as stronger evidence for isiZulu in
this local comparison. The panel suggests isiZulu, but the transcript also has
nearby tokens marked isiXhosa. The researcher sees both the form-level evidence
and the contextual caution. If the speaker is moving between varieties, a memo
may be better than a forced single label.

Example 3 (# fictional example): A Sesotho-Setswana utterance contains a shared
word that appears in both languages. The disambiguator finds no distinctive
feature and returns "insufficient evidence." This is a successful outcome. It
means the software did not invent certainty. The researcher can code the token
manually after considering speaker identity, place, topic, and surrounding
grammar.

Example 4 (# fictional example): A project includes Sepedi, Sesotho, and
Setswana. The three-way `nso_vs_sot_vs_tsn` dictionary produces low-confidence
rankings because the token is short and the context is mixed. The panel shows
all candidate languages with evidence tags and tells the researcher that the
suggestion is weak. The correct action may be to keep the token as `unknown`,
`mixed`, or a project-local tag until more context is available.

## Reading the Side Panel

When a token has a sister-language tie, the annotation editor shows a compact
dropdown beside the token. Selecting "Why this language?" opens the
disambiguator panel. The header shows the token surface form and the candidate
pair, such as `zul <-> xho` or `sot <-> tsn`. The body shows ranked candidate
languages, a confidence bar, and evidence tags. The footer shows the source
field from the active YAML dictionary.

Read the confidence bar as an audit trail, not as a probability of truth. A high
score means several local cues matched the dictionary. It does not mean the
software knows the speaker's identity, intention, or social meaning. A low score
means the software found little distinctive evidence. In either case, the
researcher can accept, override, or keep the ambiguity. Overrides are saved in
the project database and written to the provenance log so that later exports can
show which labels were automatic suggestions and which were researcher choices.

## Editing Project-Local YAML

The shipped dictionaries are starting points. They are not sacred. Every project
may keep local overrides inside the project folder, usually under a project
dictionary directory copied from the bundled YAML. This matters because interview
projects often involve local spellings, participant-preferred labels,
institution-specific terminology, or community reviewers who identify a better
analysis.

To edit a project-local dictionary, use Project Settings, open the active
sister-language dictionary, and copy the bundled entry into the project-local
override area. Change only the fields your project can justify. Keep
`verified: false` for entries that have not been checked by a language expert or
reference grammar. Use the `note` field to explain who suggested the change,
what evidence supports it, and whether it is project-specific. Never replace a
community judgement with a silent global edit. If a reviewer disagrees, record
the disagreement through the community review workflow rather than averaging the
views away.

For publications, cite both the reference grammars and your local review process.
A methods sentence might say: "Sister-language suggestions were generated from
local YAML dictionaries based on published grammars and then reviewed manually;
ambiguous cases were retained rather than forced into a single label" (Poulos &
Msimang, 1998; Du Plessis & Visser, 1992; Cole, 1955; Mesthrie, 2002).

This documentation should be read alongside
[mixed-code variety guidance](mixed_codes.md), because some ambiguous tokens are
not simply mistakes between two standard languages. They may belong to local
repertoires where standard labels are only partly adequate.
