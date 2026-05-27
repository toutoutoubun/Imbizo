# PRINCIPLES.md

Imbizo-CS Workbench is built for humanities and social-science researchers who
work with multilingual interview data in South Africa and comparable contexts.
It is not a cloud platform, not a commercial AI assistant, and not a tool that
asks researchers to surrender their data in exchange for convenience. It is a
local research workbench: careful, auditable, modest in its assumptions, and
designed around the interpretive authority of the scholar and the linguistic
dignity of the communities represented in the data.

## The Political Economy Of Research Software In Low-Resource Contexts

Many research tools silently assume global-North infrastructure: reliable
broadband, institutional subscriptions, high-end laptops, centralized storage,
and English-medium technical support. Those assumptions are not neutral. They
shape who can participate in scholarship, whose data can be safely studied, and
which languages are treated as first-class research objects. A tool for
South African code-switching research must begin from different ground.

Bandwidth can be scarce, electricity can be unreliable, and institutional
licenses may be unavailable to independent researchers, community language
workers, and students. Even when commercial cloud systems are technically
available, ethics protocols, consent agreements, and community expectations may
prohibit uploading interviews to remote services. The CARE Principles for
Indigenous Data Governance remind us that data governance is not only about
openness; it is also about collective benefit, authority to control,
responsibility, and ethics (Carroll et al., 2020). Decolonial computing asks
software builders to notice the power relations embedded in technical defaults
(Ali, 2016). Postcolonial digital humanities work likewise warns against
platform capture, where scholarly practice becomes dependent on systems whose
values and governance sit elsewhere (Risam, 2018).

Imbizo-CS therefore treats low-resource compatibility as a scholarly design
principle, not a reduced feature tier. The minimum target is a CPU-only laptop
with 4-8 GB RAM. A researcher should be able to create a project, import ELAN
or Praat data, annotate code-switching, compute metrics, and export results
without an internet connection, account, API key, telemetry, or subscription.

## Why Offline-First Is A Methodological Commitment

Offline-first is sometimes mistaken for nostalgia. For Imbizo-CS it is a
methodological commitment. Interview data is not generic text. It may contain
personal stories, religious reflection, classroom interaction, political speech,
health information, family histories, and linguistic material that communities
have not consented to place in remote systems. A workbench for such material
must make local custody the default.

Every project is a folder. Structured data is stored in one SQLite database
inside that folder; media, transcripts, dictionaries, logs, caches, and exports
are plain local files. Imports copy source files into the project folder and
never modify the originals. Exports are local. Provenance is append-only JSONL
plus database records. This is not simply implementation convenience: it makes
projects inspectable, portable, archivable, and reproducible.

No background network calls are allowed in core workflows. There is no update
check, analytics client, cloud sync daemon, license server, hosted model, or
remote font. Optional plug-ins may later support explicitly chosen external
resources, but the core application must remain useful when all plug-ins are
absent. Any future pull request that makes internet access necessary for core
work is a regression.

## Why Automation Is Auxiliary, Not Authoritative

Code-switching analysis is interpretive scholarly work. The app may assist with
language identification, switch detection, morphology suggestions, and
quantitative summaries, but it must not pretend that automatic labels are final.
The annotation model supports Matrix Language and Embedded Language,
Myers-Scotton's Matrix Language Frame, the Morpheme Order Principle, the System
Morpheme Principle, the 4-M model, borrowings, insertions, alternations, Clyne's
trigger coding, Poplack's constraints, Muysken's typology, and
Conversation-Analytic memos (Myers-Scotton, 1993; Myers-Scotton, 2002; Clyne,
2003; Poplack, 1980; Muysken, 2000; Auer, 1998). It supports these frameworks;
it does not enforce one theoretical school.

Automatic labels are marked `auto`, stored separately from manual labels, and
logged with layer, provider, version, confidence, timestamp, target item, and
input context. Manual annotations are authoritative. An automatic process must
not silently overwrite a manual decision. Imperfect analysis must never block
scholarly progress: a researcher can continue annotating with unknown, mixed,
borrowing, proper noun, or user-defined labels even when LID resources are
missing or uncertain.

Quantitative metrics follow the same ethic. M-index, I-index, burstiness,
switch density, trigger tables, and KWIC concordance are computed locally and
documented with formulas and input counts (Barnett et al., 2000; Guzman et al.,
2017; Goh & Barabasi, 2008). Metrics are not interpretations; they are
reproducible views over the current annotation state.

## Why Bantu Morphology Cannot Be Reduced To Whitespace Tokenization

Bantu-language code-switching often requires attention below the whitespace
token. Prefixes, agreement markers, negation, tense/aspect morphology, and
borrowed or inserted roots may interact in ways that matter for Matrix Language
Frame analysis and related approaches. Treating whitespace tokenization as a
complete linguistic analysis would erase exactly the structure many researchers
need to study. South African language-resource work by SADiLaR and others
shows both the value and the difficulty of developing resources for these
languages (Eiselen & Puttkammer, 2014). Work on South African low-resource
languages and multilingual contexts further underscores why morphology-aware
support matters (Mabokela & Schlippe, 2022).

The MVP therefore does not bundle a full morphological analyzer. Instead, it
allows manual morpheme splitting and provides editable project-local
dictionaries for common prefixes, negation markers, tense/aspect markers, and
related forms for isiZulu, isiXhosa, Sesotho, and Setswana. Suggestions are
displayed as suggestions, never forced segmentations. Manual segmentation
history is preserved per token.

## Why Morphology Matters

Whitespace tokenization is a convenient habit, but it is not a neutral
description of Bantu languages. It comes from writing systems, school
grammars, colonial-era standardization, and software traditions that often
treat the space-delimited word as the obvious unit of analysis. For languages
where prefixes, concords, extensions, tense/aspect markers, locatives, and
borrowed stems interact inside and around the written word, that assumption can
flatten the very structure under study. A local workbench for South African
code-switching must not pretend that what is easy for a tokenizer is the same
as what is meaningful for a researcher (Demuth, 2000). The first question
should be what the research situation requires, not what a generic NLP pipeline
can count most quickly.

Surface Matrix Language and Embedded Language labels are useful, but on their
own they underdetermine what is happening in the data. If a token contains an
English-origin stem inside an isiZulu or Sesotho frame, the language label can
tell us where the stem comes from. It cannot tell us whether the stem has been
drawn into a noun-class pattern, whether concord agreement links it to
surrounding material, whether a system morpheme comes from the host grammar, or
whether the example is better understood as alternation, insertion, borrowing,
or something more locally specific. Poplack's constraint-based tradition,
Muysken's typology, and Myers-Scotton's Matrix Language Frame model ask
different questions, but all of them become weaker if the evidence is reduced
to whole-token language labels (Poplack, 1980; Muysken, 2000;
Myers-Scotton, 1993; Myers-Scotton, 2002).

The 4-M model is therefore not decorative metadata. It is the minimum
interpretive infrastructure needed to make many MLF claims testable rather
than assertional. If a researcher says that one language supplies the
grammatical frame, the project should be able to show which morphemes were
treated as content morphemes, which were treated as early system morphemes,
which were treated as bridge or outsider late system morphemes, and which
concord links support or complicate that reading. The software must help make
the chain of evidence visible. It must not replace the chain of reasoning with
a single opaque label.

The v1.0 integration score follows the same principle. It is exposed,
documented, and editable because the researcher's theoretical position is not
the software's to decide. A scholar working in a Poplack-informed account may
weight evidence differently from a scholar using Muysken's typology or an MLF
account. A community researcher may decide that local speaker judgment matters
more than a shipped dictionary. The app should support that decision by
showing the weights, recording provenance, and exporting enough data for
readers to reconstruct the calculation. A hidden score would be faster to
present, but less honest.

Future contributors must be especially careful here. It will always be
tempting to "improve accuracy" by hardcoding a theoretical assumption: to make
one concord pattern automatically prove a Matrix Language, to treat a prefix as
unambiguously one class in every variety, or to collapse Tsotsitaal, Iscamtho,
Kaaps, and other local practices into standardized-language expectations. That
kind of improvement would be an erosion of the project. Accuracy without
interpretive humility is not accuracy in humanities research.

Morphology-aware design is also part of the decolonial posture of this
codebase. Decolonial computing asks us to examine the power relations embedded
in technical defaults (Ali, 2016). The CARE Principles remind us that
communities have authority over how data about them is governed and interpreted
(Carroll et al., 2020). Postcolonial digital humanities critiques warn against
platforms that absorb local knowledge into generic categories (Risam, 2018).
For Imbizo-CS, respecting those warnings means refusing to let a tokenizer, a
dictionary, or a metric silently settle a question that belongs to the
researcher and the speech community.

## Why Bundled ASR Is Deferred

Automatic speech recognition is valuable, but bundled high-end ASR would
violate the low-resource promise of the MVP. South African code-switching ASR
work, including Kaldi-based systems, demonstrates the computational and data
demands involved in building robust systems for multilingual speech (Yilmaz et
al., 2018). Shipping heavy ASR as a default dependency would increase install
size, memory requirements, and maintenance burden, while also risking a false
sense of accuracy in precisely the contexts where researchers need careful
manual review.

Imbizo-CS provides a clean optional ASR plug-in interface for future local
providers such as Whisper.cpp, Vosk, or Coqui STT. These may be installed from
local files by researchers who understand the resource cost and consent
conditions. Manual transcription remains the default.

## Why We Refuse Cloud LLM Dependencies By Default

Cloud LLM systems can be useful in some research workflows, but they are not
acceptable as a core dependency for this project. They require network access,
often involve opaque data handling, may impose account or subscription
requirements, and can shift interpretive authority from the researcher to a
black-box service. For sensitive interview data, these defaults are
unacceptable.

The codebase may later expose an explicit plug-in door for informed-consent
uses, such as local-only synthetic data augmentation or carefully reviewed
optional assistance. Such plug-ins must be off by default, clearly labelled,
auditable, removable, and governed by project ethics. Cloud LLM integration
must never become necessary for project creation, annotation, metrics, or
export.

## Citable And Reproducible Research Software

Imbizo-CS follows the spirit of FORCE11 software-citation principles and
FAIR4RS: software should be identifiable, citable, versioned, and connected to
the research outputs it helps produce (Smith et al., 2016; Chue Hong et al.,
2022). Every export includes a citation snippet and a DOI placeholder until a
real project DOI is minted. Every automatic decision, manual override, metric
run, import, and export is logged with provenance. A project zip should allow
another machine running the same Imbizo-CS version to reconstruct the analysis
from local data.

## License Choice: GPLv3-Or-Later

Imbizo-CS Workbench is licensed under GPLv3-or-later. This is a deliberate
choice. GPLv3 protects the freedom of researchers, community language workers,
and future contributors to inspect, modify, share, and improve the tool. It
also discourages a future proprietary fork from enclosing community-funded or
community-relevant research infrastructure. AGPLv3 was considered, but the MVP
is a local desktop application rather than a network service. If future
server-like components are ever proposed, AGPLv3 may be reconsidered for those
components. For the offline desktop workbench, GPLv3-or-later is the right fit.

## Pledge To Future Contributors

The principles in this document are not decorative. They are the constitution
of the codebase. Future pull requests must be evaluated against them. A feature
that weakens offline operation, data sovereignty, interpretive authority,
linguistic dignity, or reproducibility is not progress. It is erosion.

We build for researchers who may be working without institutional
infrastructure, with sensitive data, in multilingual communities whose speech
has too often been treated as peripheral. The defaults of this software must
honour that reality. Offline-first is a promise. Manual override is a promise.
No telemetry is a promise. Open, citable, reproducible local research software
is the promise this repository exists to keep.
