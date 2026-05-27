# Phonological Integration in Imbizo-CS v1.5

Borrowing and code-switching are not always separated by a bright line. A word
from one language may appear inside another language's grammar, receive local
pronunciation, take local morphology, and become ordinary in a community. Or it
may remain recognizably foreign in a particular utterance. v1.5 adds optional
phonological evidence so researchers can describe this continuum more carefully
(Poplack, 1980; Muysken, 2000; Mesthrie, 2002).

## What Phonology Adds

v1.0 already allowed researchers to mark noun class, concord, and 4-M evidence.
That tells us whether a word is morphologically and syntactically integrated
into the host frame. For example, a foreign-language stem may receive a Bantu
noun-class prefix and agree with an adjective. But integration can also be heard
in sound. A borrowed word may add vowels to fit local syllable patterns, simplify
clusters, receive local stress, or be assigned tone. Bantu tone systems are
complex, and tonal analysis requires care, but tone can be part of how words
become locally adapted (Hyman, 2003).

Phonological evidence is optional because not every project has audio, and not
every researcher wants to make phonetic claims. A transcript-only project can
leave these fields blank. A project with audio but no trained phonetician can
record only what is audible and mark uncertainty. The software never requires
phonological annotation to compute ordinary v1.0 metrics.

## Common Evidence Types

The following examples are fictional or paraphrased and should be verified
against project audio and relevant literature before publication.

Vowel epenthesis (# fictional example): A consonant-heavy English word is
pronounced with an added vowel in a Bantu-language frame. The researcher may mark
`vowel_epenthesis` and add a note such as "audible final vowel in this token."
This suggests adaptation, but it does not by itself prove the word is a stable
borrowing.

Cluster simplification (# fictional example): A consonant cluster is reduced or
broken in speech. The researcher can mark `cluster_simplification` if the audio
supports it. If the transcript does not capture pronunciation, leave the field
blank or mark uncertainty.

Tonal reassignment (# fictional example): A word appears to receive a tonal
pattern consistent with the host language. Because tone analysis is specialized,
the feature should usually be marked `verified: false` or reviewed by someone
with relevant training unless the project design explicitly includes tone
annotation (Hyman, 2003).

Stress shift (# fictional example): A borrowed word is pronounced with stress or
rhythmic placement different from the source-language form. This may matter in
Afrikaans-English or English-Bantu contact settings, but it should be documented
from audio, not guessed from spelling.

## Marking Features Without an Audio-Trained Ear

The safest rule is: mark what you can hear, say what you cannot know. If you are
not trained in phonetics, you can still record careful observations. Use the
checkboxes in the Phonological Evidence sidebar only when the feature is audible
or visible in a reliable transcript convention. Add a plain-language note. For
example: "Speaker appears to add a final vowel; uncertain because background
noise overlaps." That kind of note is more useful than a confident but hidden
assumption.

If a feature comes from a dictionary suggestion, remember that dictionary
patterns describe possible adaptations. They do not confirm that the speaker did
that in this token. Accepting a feature should mean that the researcher has
checked the token, not that the software found a pattern in the abstract.

## Integration Score v2

Borrowing Integration Score v2 combines the v1.0 morphological score with
optional phonological evidence. The score remains a transparent weighted sum.
Typical factors include noun-class marking, confirmed concord links, repeated
project frequency, and phonological observations such as vowel epenthesis or
cluster simplification. The weights are project-editable because different
theoretical traditions value different kinds of evidence (Poplack, 1980;
Muysken, 2000).

Do not treat the v2 score as a verdict. A high score means the project has more
recorded evidence of integration. A low score may mean the word is less
integrated, or simply that the project did not annotate audio evidence. In
methods writing, report the weights used and the evidence types available. The
formula-transparency block in v1.5 reports exists for exactly that reason.

## Practical Workflow

Start with a token already marked as a non-host stem inside a host frame. Open
the Phonological Evidence sidebar. Check only features you can support from the
audio, transcript, or a reviewed project note. Add uncertainty notes generously.
If the same feature appears across many tokens, use bulk edit carefully and
review a sample afterward. Recompute Integration v2 only after the evidence is
saved.

For publication, include both presence and absence of evidence. A responsible
sentence might read: "Integration v2 included noun-class and concord evidence
for all tokens; phonological features were marked only where audible in the
recording, and uncertain tonal observations were excluded from the score"
(Poplack, 1980; Muysken, 2000; Hyman, 2003).
