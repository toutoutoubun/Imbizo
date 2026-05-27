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
