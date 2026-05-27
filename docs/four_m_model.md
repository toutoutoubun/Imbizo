# docs/four_m_model.md

# The 4-M Model In Imbizo-CS v1.0

The 4-M model is a way of thinking about morphemes in bilingual speech. A
morpheme is a meaningful piece of language: a root, a prefix, a suffix, a
concord marker, a plural marker, or another small grammatical form. The model
matters because code-switching is not only about which whole words come from
which language. It is also about which parts of grammar carry the frame of an
utterance.

Imbizo-CS v1.0 supports the 4-M model because many researchers use Matrix
Language Frame analysis to ask whether one language provides the main
grammatical frame while another contributes embedded material
(Myers-Scotton, 2002). The software supports this question but does not force
it. You may leave 4-M fields unassigned, use them only for selected examples,
or interpret the same evidence through another framework.

## The Intuition Behind The Model

The 4-M model divides morphemes into four broad types: content morphemes,
early system morphemes, bridge late system morphemes, and outsider late system
morphemes. The names can sound technical, but the intuition is straightforward.
Some morphemes carry concrete lexical meaning, like "book", "buy", "person",
or a verb root. Others do grammatical work around those meanings. Some of that
grammatical work is closely tied to the word itself. Other grammatical forms
depend on a larger phrase or clause (Myers-Scotton, 2002; Jake,
Myers-Scotton & Gross, 2002).

This matters for MLF claims because Matrix Language analysis is not just a
surface statement such as "the sentence feels mostly isiZulu." The System
Morpheme Principle asks whether certain system morphemes come from the Matrix
Language. If we do not tag morpheme types, that claim remains rhetorical. With
4-M tags, the claim becomes testable against your annotated data
(Myers-Scotton, 2002).

## The Four Types

Content morphemes are lexical material. They carry referential or descriptive
meaning. In English, examples might include `book`, `buy`, or `student`. In
Afrikaans, examples might include `boek` or `koop`. In isiZulu, a researcher
might tag a noun stem or verb root as content. In Sesotho, a noun such as
`motho` or a verb root may be treated as content. These examples are
documentation examples only; verify all real examples in your project.

Early system morphemes are grammatical forms that are selected together with a
content morpheme. A plural marker tied to a noun is a common teaching example.
In Bantu-language work, noun-class prefixes may often be candidates for early
system analysis, but this depends on the segmentation and the theoretical
question. Do not tag all prefixes automatically. The point of Imbizo-CS is to
record a reviewed decision.

Bridge late system morphemes connect larger pieces inside a phrase. In English,
`of` can be used as a simple example of a linker. In Afrikaans, `van` may serve
as a comparable teaching example. In Bantu languages, possessive or associative
linkers may be considered, but their analysis requires attention to the
language and construction. The shipped dictionaries mark many such entries
`verified: false` because they are hints, not a grammar.

Outsider late system morphemes depend on information outside their immediate
content morpheme. Agreement markers are often discussed here. In Bantu
code-switching analysis, subject concords, object concords, or other agreement
forms can be especially important because they may show which grammar is
structuring a mixed utterance. That is why v1.0 connects the 4-M layer to
concord links and the MLF audit report (Jake, Myers-Scotton & Gross, 2002).

## Examples Across Languages

The following examples are simplified teaching examples. They are not
publication-ready claims.

```text
English: book
Type: content
# fictional or paraphrased; verify with a reference grammar for publication
```

```text
Afrikaans: van
Type: bridge_late_system candidate
# fictional or paraphrased; verify with a reference grammar for publication
```

```text
isiZulu: u- as a subject-concord candidate
Type: outsider_late_system candidate
# fictional or paraphrased; verify with a reference grammar for publication
```

```text
Sesotho: ba- as an agreement or class-prefix candidate depending on context
Type: early_system or outsider_late_system candidate after review
# fictional or paraphrased; verify with a reference grammar for publication
```

The last example shows why Imbizo-CS avoids automatic certainty. The same
surface string can participate in different constructions. The researcher
must decide what it is doing in the utterance.

## Worked Example: One Fictional isiZulu-English Utterance

Take the fictional line from the v1.0 data-model example:

```text
Ngithenge i-laptop entsha izolo.
# fictional or paraphrased; verify with a reference grammar for publication
```

Step 1: label the token languages. A researcher may label `Ngithenge`,
`entsha`, and `izolo` as isiZulu, while treating the stem in `i-laptop` as
English-origin. This is only the surface layer.

Step 2: review noun class. The Noun Class panel may suggest class 9 for
`i-laptop`, based on a prefix match. The researcher accepts or overrides the
class. If accepted, the token now has a reviewed noun-class analysis.

Step 3: inspect concord. The researcher clicks "Show concord candidates" and
reviews `entsha` as a possible adjectival concord relation. If confirmed, the
project records a concord link between `i-laptop` and `entsha`.

Step 4: tag 4-M types. The researcher might tag the English stem as `content`,
the noun-class prefix as an early system morpheme if it has been manually split,
and the concord material as a system morpheme. The precise tagging depends on
the segmentation chosen for the project.

Step 5: read the audit. The MLF audit report gathers the reviewed 4-M tags and
asks whether system morphemes appear to point to one Matrix Language. If they
do, the report may say `consistent`. If system morphemes point in different
directions, it may say `mixed`. If too little has been tagged, it says
`insufficient_data`. None of these verdicts is a conclusion by itself. They are
prompts for interpretation.

## Why This Matters

Without 4-M tagging, Matrix Language claims can become impressionistic. A
researcher may say that an utterance is isiZulu-framed, but the claim is hard
to inspect. With 4-M tagging, the reader can see which tokens were treated as
content morphemes, which as system morphemes, and which concord links were
confirmed. This makes MLF claims more empirical: not automatic, not final, but
grounded in visible annotation decisions (Myers-Scotton, 2002).

This is also useful when the evidence does not support a clean MLF account.
Slabbert and Myers-Scotton show that South African urban code-switching and
in-group varieties may have social and structural patterns that resist simple
classification (Slabbert & Myers-Scotton, 1997). The `mixed` verdict is not a
failure. It is a way of saying: this utterance deserves closer human reading.

## Reading The MLF Audit Report

The MLF audit report has three main parts. First, a summary counts utterances
as `consistent`, `mixed`, or `insufficient_data`. Second, a table shows each
utterance with its timestamp, speaker, 4-M distribution, and recommended review
action. Third, a drill-down section lists the evidence for utterances marked
`mixed`: token IDs, surfaces, language labels, 4-M tags, and notes.

Use the report as a navigation tool. It helps you find utterances worth
discussing in a chapter, article, or appendix. It does not replace close
reading, conversation analysis, speaker knowledge, or theoretical judgment.
For noun-class background, see [noun_classes.md](noun_classes.md).

