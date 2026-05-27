# docs/noun_classes.md

# Noun Classes In Imbizo-CS v1.0

This guide explains the noun-class tools added in Imbizo-CS Workbench v1.0. It
is written for researchers who know that isiZulu, isiXhosa, Sesotho, and
Setswana are Bantu languages, but who may not have studied noun-class systems
in detail. The short version is this: in many Bantu languages, nouns belong to
classes, and those classes can shape other words around the noun. In
code-switching research, this matters because a foreign-language word may be
treated as if it belongs to the host language's grammar.

## What Is A Noun-Class System?

In English, nouns do not normally carry a rich class prefix. We can say "a
student", "the student", "new student", or "students", and most of the
grammatical work is done by separate words or by a plural ending. Bantu
languages often organize nouns differently. A noun may have a prefix that
places it in a noun class. That class can be associated with broad semantic
tendencies such as humans, abstract qualities, languages, infinitives, mass
nouns, or locatives. These meanings are tendencies, not perfect boxes. A class
is grammatical, and real words often have histories that do not fit a simple
semantic label.

For example, a class may include many human nouns, while another class may
include language names or instruments. In Southern Bantu languages, noun-class
systems are part of a larger agreement system: a noun's class can affect forms
on adjectives, demonstratives, possessives, relatives, verbs, and other linked
material (Poulos & Msimang, 1998; Du Plessis & Visser, 1992; Demuth, 2000).
This is why noun-class annotation in Imbizo-CS is not just a label on the noun.
It is a way of tracing how a phrase is built.

The shipped dictionaries in v1.0 are starter dictionaries. They are small,
local YAML files and many entries are deliberately marked `verified: false`.
This is not a defect. It is an honesty mechanism. Bantu noun-class systems are
not identical across isiZulu, isiXhosa, Sesotho, and Setswana, and actual
speech may include non-standard varieties, loanwords, urban repertoires,
orthographic variation, and local speaker preferences. A dictionary suggestion
is a prompt for review, not an authority.

## Why Noun Classes Matter For Code-Switching

In code-switching analysis, a surface language label tells us only part of the
story. If a researcher labels a token as English inside an isiZulu utterance,
that label says something about the origin or conventional form of the word.
It does not yet tell us how that word is functioning grammatically. A foreign
stem may be sitting as a bare insertion, or it may be integrated into a host
Bantu frame through a noun-class prefix and concord patterns.

Consider a fictional isiZulu-English example:

```text
Ngithenge i-laptop entsha izolo.
# fictional or paraphrased; verify with a reference grammar for publication
```

The stem "laptop" is English. But if the researcher analyzes `i-laptop` as
carrying class 9 behavior and finds a concord relation with `entsha`, the
analysis becomes richer. The question is no longer only "Where is the English
word?" It becomes "How is this English stem being incorporated into the
isiZulu grammatical frame?" That is the kind of question v1.0 makes visible.

This distinction matters for debates about insertion, borrowing, alternation,
and matrix-language structure. Imbizo-CS does not decide the theory for you.
It gives you local fields where you can record the evidence: noun class,
prefix, concord links, 4-M tags, and memos. You may then interpret that
evidence through the framework you use in your thesis or article.

## Fictional Worked Examples

The following examples are documentation examples only. They are not reference
grammar claims.

### isiZulu

```text
Ngithenge i-laptop entsha izolo.
# fictional or paraphrased; verify with a reference grammar for publication
```

A researcher may select `i-laptop`, manually split the prefix `i-`, and ask
Imbizo-CS for noun-class suggestions. The side panel may suggest class 9
because the shipped isiZulu dictionary includes `i-`, `in-`, `im-`, and related
forms as possible class 9 prefixes. If the researcher accepts class 9 and then
confirms a concord link to `entsha`, the project records the class assignment,
the matched prefix, the concord relation, the dictionary version, and the
provenance event. The app does not claim that all `i-` words are class 9. It
records a reviewed analysis for this token in this project.

### isiXhosa

```text
Ndibone i-fax entsha eofisini.
# fictional or paraphrased; verify with a reference grammar for publication
```

In this fictional example, `i-fax` may be treated as an English-origin stem
inside an isiXhosa frame. The isiXhosa starter dictionary may offer a class 9
candidate for `i-`, but several similar prefixes can occur across classes or
orthographic contexts. The researcher should check the phrase, surrounding
agreement, and their reference grammar before accepting the suggestion
(Du Plessis & Visser, 1992). If the speaker is using a non-standard or urban
variety, the memo field is a good place to record that the analysis is local
to the project.

### Sesotho

```text
Ke bone di-file tse ntjha kajeno.
# fictional or paraphrased; verify with a reference grammar for publication
```

Sesotho uses a noun-class system that differs from Nguni languages in form and
orthographic convention. A researcher might inspect `di-file` as a possible
plural form in a Sesotho frame, then look for concord material such as `tse`.
The noun-class panel may provide a starting point, but it must not be treated
as a replacement for reference grammar or speaker knowledge (Demuth, 2000;
Mojapelo, 2007). In v1.0, unverified dictionary entries are displayed with
their warning notes, so the researcher can decide whether to accept, override,
or leave the token unassigned.

### Setswana

```text
Ke bone di-store tse dintsi mo toropong.
# fictional or paraphrased; verify with a reference grammar for publication
```

Setswana is related to Sesotho but is not identical to it. One of the limits of
v1.0 is that sister-language disambiguation is still conservative. The app does
not try to decide whether an ambiguous form belongs to Sesotho or Setswana.
Instead, it shows the dictionary registered for the language label you have
chosen and lets you record your own analysis. This is especially important in
multilingual interviews where speakers may move across related languages or
local varieties (Cole, 1955; Maho, 1999; Guerois, 2014).

## Reading The Noun-Class Side Panel

When you select a token inside a Bantu-tagged span, the Noun Class side panel
shows the token surface and the active language tag. Below that, it lists
ranked class candidates from the local dictionary. Ranking is based on simple
prefix matching. Longer exact prefix matches are shown before shorter matches.
No machine learning model is used.

Each candidate row shows:

- class number
- matched prefix
- semantic-domain note
- verification status
- dictionary note, if present
- `Accept` and `Override` buttons

Choose `Accept` when the suggestion matches your analysis. Choose `Override`
when the class is wrong, too broad, or too uncertain. Override lets you enter a
different class, prefix, and memo. The decision is written into the project
database and recorded in provenance. If you are unsure, leaving the field blank
is valid scholarly work. Incremental knowledge-building is better than a false
certainty.

The "Why this class?" footer expands to show the dictionary `source`, the
matched prefix, and any caution note. Use this text when preparing a methods
appendix. It helps readers see that the software did not silently invent the
analysis.

## Editing Project-Local Dictionaries

Shipped dictionaries are starter resources. Your project can override them
without changing the application for everyone else. Project-local dictionaries
live inside your project folder:

```text
project/
  dictionaries/
    noun_classes/
      zul.yaml
      xho.yaml
      sot.yaml
      tsn.yaml
```

To edit a dictionary, copy the shipped YAML file into the matching project
folder and change only the entries you want to review. Keep the required
metadata fields: `language_code`, `language_name`, `version`, `source`,
`last_reviewed_by`, and `last_reviewed_on`. When you add an entry that has not
been checked against a cited grammar or speaker review, set
`verified: false` and add a `note`. That note is part of the research record.
It will travel with project exports.

Do not use the dictionary to force all future projects into your analysis. A
dictionary choice belongs to a project because it reflects the corpus, speakers,
ethics, and theoretical commitments of that project. If you later publish a
community-reviewed improvement, it can be proposed upstream, but the local
project override remains the safest place for live research decisions.

For a deeper explanation of how noun-class evidence connects to 4-M and MLF
analysis, see [four_m_model.md](four_m_model.md).

