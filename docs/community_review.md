# Community Review Workflow in Imbizo-CS v1.5

Community review is not an accessory to Imbizo-CS. It is part of the research
method. The software ships dictionaries for sister-language cues, trigger
candidates, mixed-code profiles, and phonological patterns, but those files are
starting points. They cannot substitute for local knowledge, speaker judgement,
or community accountability. v1.5 therefore adds an offline review packet
workflow so dictionary and annotation review can happen even when collaborators
do not share a cloud platform or continuous internet access.

## Why Review Belongs in the Design

Language technologies often present dictionaries and models as if they were
neutral infrastructure. In low-resource and postcolonial contexts, that is a
dangerous fiction. The choice to include a form, spell it one way, mark it as
verified, assign it to a variety, or treat it as a trigger can affect how a
community is represented. The CARE Principles emphasize collective benefit,
authority to control, responsibility, and ethics for Indigenous data governance
(Carroll et al., 2020). Decolonial computing asks us to notice how software
systems can reproduce extractive or global-North assumptions even when they look
technically helpful (Ali, 2016; Risam, 2018).

In Imbizo-CS, community review means that dictionary entries and sensitive
annotations can be inspected by people with relevant linguistic, cultural, or
project knowledge. It does not mean outsourcing responsibility to one person.
It means creating a record of who reviewed what, what they suggested, what was
accepted or rejected, and why.

## Offline Review Packets

The workflow is designed for USB transfer. A researcher chooses "Send to
community review" and selects target kinds, such as `dictionary_entry`,
`mixed_code_span`, or `phonological_feature`. Imbizo-CS creates a zip packet
containing a manifest, a human-readable diff, a machine-readable diff, a local
signature hash, and reviewer instructions. No network call is made.

The reviewer opens the packet on their own machine, reads the plain-language
diff, adds comments or proposed changes, and returns the packet by USB or other
local transfer. When the researcher imports the packet, Imbizo-CS verifies the
signature hash to detect accidental tampering. By default, imported reviews are
queued as pending. They are not auto-applied.

This matters because review is interpretive work. A packet may contain a strong
suggestion, a disagreement, a caution about stigma, or a request to use a
participant-preferred label. The researcher should read it before applying it.

The packet should contain only what the reviewer needs. Do not export a whole
interview when a dictionary entry is enough. Do not include participant
identifiers if a pseudonym or excerpt ID will do. Offline transfer does not
remove consent obligations. It simply avoids cloud infrastructure.

## Reviewer Aliases

Reviewer aliases protect privacy while preserving accountability. A reviewer may
choose an alias such as `reviewer_zul_01` or a community-agreed name. The alias
is not meant to prove legal identity. It helps the project distinguish comments
from different reviewers without exposing personal details in exported reports.

Aliases are especially important when reviewers comment on stigmatized
varieties, community-sensitive vocabulary, or politically charged language
labels. A reviewer should not be forced to attach a public name to every
correction. At the same time, the project should not erase the fact that review
happened. The alias is a practical compromise.

## Recording Disagreement

Imbizo-CS does not average disagreements away. If one reviewer says a dictionary
entry is appropriate and another says it is harmful or regionally wrong, the
project should preserve both comments. The maintainer can accept one change,
reject another, or mark an entry as disputed. A disputed note is often more
honest than a falsely clean dictionary.

This approach is important for mixed-code varieties. Tsotsitaal, Iscamtho,
Kaaps, and Sabela are not static lists. They are socially situated practices,
and people may disagree about names, boundaries, spelling, and ownership. A
software tool should not settle those questions by majority vote. It should make
the disagreement visible enough for responsible interpretation.

Governance asymmetry still matters. A university researcher may control the
laptop, project deadline, and final publication, while reviewers contribute
knowledge under time pressure. The workflow cannot solve that imbalance by
itself. It can, however, make review labor visible, preserve dissent, and help a
project avoid pretending that a dictionary was community-reviewed when only one
person had a brief chance to comment.

## Applying a Review

When an incoming packet is selected, the Community Review pane shows signature
verification, target kind, reviewer alias, status, and human-readable diff. The
researcher can apply, reject, or defer the item. Applying requires a mandatory
comment. That comment should explain why the change fits the project. Rejection
also requires a comment. This keeps the audit trail useful for later methods
writing.

Auto-apply exists only as an explicit advanced action and should be rare. It is
logged in provenance. The default queue protects against accidental overwriting,
especially when a packet was created for one project context and later imported
into another.

## Methods and Ethics

A project that uses community review should say so in its methods section. It
can describe the number of reviewers, their aliases or roles, the kinds of
entries reviewed, and how disagreements were handled. It should not imply that a
single reviewer authorized a whole language community. Where CARE-aligned
governance is possible, decisions about dictionary publication, sharing, or
reuse should respect collective authority and project consent (Carroll et al.,
2020).

Review packets also support researchers with unstable connectivity. A reviewer
can work offline, on a borrowed laptop, in a community office, or wherever data
sovereignty and consent allow. That is not a workaround. It is part of the
principle that research software should meet researchers and communities where
they are, rather than requiring cloud accounts, constant bandwidth, or platform
capture (Ali, 2016; Risam, 2018).
Local review remains real review.

## Practical Checklist

Before sending a packet, confirm that the target data may be shared with the
reviewer under your consent and ethics terms. Remove unrelated sensitive
materials. Include enough context for a fair review. After import, read each
comment before applying. Preserve rejected or disputed comments when they are
methodologically meaningful. Export the review history only when it is ethical
to do so.

Community review is slow work. That slowness is a strength. It keeps linguistic
dignity, data sovereignty, and interpretive authority in the workflow instead of
treating them as text in a principles document.

A useful closing question for every review packet is: "Could this change harm a
speaker or community if exported without context?" If the answer is yes or even
maybe, keep the comment local, add caveats, and discuss the issue before using it
in a report. The software should make careful work easier, not make risky
publication faster.
