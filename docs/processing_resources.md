# Processing Resources in Imbizo-CS

Imbizo-CS can now bootstrap not only dictionaries, but also processing
resources: language-identification models, corpora, part-of-speech and
named-entity datasets, pronunciation resources, and optional local ASR. These
resources are not hidden cloud services. They are files on your own machine,
downloaded once on a connected computer or reconstructed from an offline bundle,
then used locally.

The most important rule is still the same: these resources support research
judgement; they do not replace it. A model score, POS tag, NER label, or ASR
transcript is evidence to inspect. It is never a final interpretation of a
speaker's language practice.

## fastText lid.176

The fastText `lid.176` model is the default lightweight baseline language
identifier for Layer 1 of the Imbizo-CS LID pipeline (Joulin et al., 2017). It
is small enough to ship in an offline bundle as `lid.176.ftz`, and it covers
Afrikaans, English, isiZulu, isiXhosa, Sesotho, and Setswana. The larger
`lid.176.bin` can be carried in a custom bundle, but the compressed model is the
default because the project is designed for 4-8 GB RAM laptops.

The model is useful for a first pass over chunks and tokens. It is not a
South-African-code-switching specialist. If it confuses sister languages, marks
a mixed token as one language, or gives high confidence for a questionable
label, the researcher can override it. The model is licensed CC-BY-SA-3.0, so
redistribution and derived bundles need to respect share-alike obligations.

## NCHLT Text Corpora

The NCHLT text corpora provide validation text, frequency lists, and named-entity
lists for South African languages (Eiselen & Puttkammer, 2014). In Imbizo-CS
they are indexed under `corpora/nchlt/<iso>/`. The index records file inventory
and simple whitespace token counts. Those counts are practical inventory
metadata, not a linguistic theory of the word.

For humanities projects, NCHLT can help answer modest questions: is a proposed
spelling common in a larger corpus, is a term rare, or does a frequency list
support a dictionary suggestion? It should not be used to overrule a speaker's
orthography or community-specific form. The NCHLT text corpora are listed here
under CC-BY-2.5-SA, so attribution is required.

## Updated Morphologically Annotated Corpora

The updated morphologically annotated corpora from the SADiLaR II extension
project provide token-level morphological analyses for several South African
languages (Gaustad & McKellar, 2024). Imbizo-CS stores them under
`corpora/morph_annotated/<iso>/` and builds a tag inventory. That tag inventory
can help noun-class and concord tools know whether a tag such as `NPre`, `NRoot`,
or `Fut` appears in the local reference material.

This does not turn Imbizo-CS into a full morphological analyzer. The corpora are
reference material and validation evidence. They help the researcher notice
patterns and compare suggestions against annotated examples.

## MasakhaPOS

MasakhaPOS, also known through AfricaPOS, provides POS-tagged CoNLL data for
African languages, including several South African languages (Dione et al.,
2023). Imbizo-CS stores it under `corpora/masakhapos/<iso>/`. POS tags can
support the 4-M model workflow by pointing to candidate content morphemes or
function-like items, but POS and 4-M categories are not the same thing.

MasakhaPOS data is CC-BY-NC-4.0. "NC" means non-commercial. If your thesis,
article, class handout, or community report includes derived tables from this
dataset, attribution is required and commercial reuse may be restricted. If your
project has any commercial partner or paid deliverable, check the license before
sharing outputs that depend on this dataset.

## MasakhaNER

MasakhaNER 2.0 provides named-entity training and evaluation data (Adelani et
al., 2022). Imbizo-CS uses it as background support for the v1.5 Trigger
Detector. Named entities can be trigger candidates in Clyne-style analysis, but
a named entity is not automatically a trigger. A proper noun near a switch point
is a prompt to inspect the excerpt, not a conclusion about cause.

MasakhaNER is also CC-BY-NC-4.0. The same non-commercial caution applies.

## ZA_LEX

ZA_LEX contains lexical pronunciation resources, including material useful for
grapheme-to-phoneme work, syllabification, and related phonological processing.
Imbizo-CS mirrors per-language directories under `processing/za_lex/<iso>/` only
when each directory keeps its upstream `LICENCE` file. This matters because
scripts and data can have different licenses.

For v1.5, ZA_LEX supports the phonological side of the Borrowing Integration
Score v2. If a foreign-language stem has vowel epenthesis, cluster
simplification, or other adaptation, that is evidence of integration. It is
still not a final judgement. A researcher may mark a feature uncertain, reject
it, or weight it differently.

## whisper.cpp ASR

whisper.cpp is optional. It is not installed by default, not required for MVP
work, and not used unless the researcher passes `--include-asr` and explicitly
sets `IMBIZO_ASR_ACCEPTED=1`. This two-step gate exists because ASR quality for
isiZulu, isiXhosa, Sesotho, Setswana, and multilingual South African interview
speech is not guaranteed. South African code-switching ASR has known resource
demands and quality challenges (Yilmaz et al., 2018). Wider 2024 reporting on
AI transcription tools also documented fabricated text and high-risk errors in
Whisper-based workflows (Associated Press, 2024).

ASR output should therefore be treated as a rough draft. It can speed up manual
transcription only if the researcher listens back, corrects, and records that
the transcript was machine-assisted. It must never be treated as authoritative
evidence about what a participant said.

## Worked Example

In the fictional isiZulu-English interview from the v1.0 examples, the token
`i-laptop` was manually tagged as a class 9 loanword candidate. With processing
resources installed, fastText can provide a first-pass LID suggestion, the
morphologically annotated corpora can show whether similar noun-prefix tags are
present in reference data, MasakhaNER can help flag nearby proper nouns as
possible trigger candidates, and ZA_LEX can support phonological observations
if the audio suggests adaptation. Each step remains inspectable and
overridable. The output is a richer audit trail, not a smarter oracle.
