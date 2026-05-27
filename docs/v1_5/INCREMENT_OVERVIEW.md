## v1.5 Deliverable 1 - Increment Overview

### 1. Plain-Language Summary

The MVP gave researchers a local, privacy-preserving place to import, annotate, search, and export code-switched interview data. Version 1.0 added grammatical depth: noun classes, concord links, and 4-M morpheme annotation. Version 1.5 now widens the interpretive frame. It adds six opt-in layers for questions that arise when South African multilingual data refuses to behave like neat language A / language B alternation: sister-language disambiguation, triggered switching, mixed-code variety mode, borrowing integration score v2, comparable subcorpus export, and community review workflow.

The Sister Language Disambiguator treats `zul` versus `xho`, and `sot` versus `tsn`, as research problems rather than tidy technical labels. In many transcripts, a token may be compatible with more than one closely related language, especially when the recording is noisy, orthography is inconsistent, or speakers draw on shared regional resources. A fast language-ID label can be useful, but it can also hide uncertainty. v1.5 therefore keeps disambiguation advisory: it can point to distinctive morphemes, click-orthography patterns, or project-local lexical notes, but the researcher decides whether a form is isiZulu, isiXhosa, Sesotho, Setswana, ambiguous, mixed, or deliberately unassigned. This matters because language labels can carry identity, place, education, generation, and politics in South African sociolinguistic work (Mesthrie, 2008).

The Triggered Switching Detector adds a different analytic lens from the Matrix Language Frame model. MLF asks how the grammar of a mixed clause is organized; triggered switching asks whether particular words, forms, cognates, discourse routines, or prior switches make another switch more likely nearby (Clyne, 1967, 2003). This is not a rival that replaces MLF. It is a separate question. A researcher may find that a switch is grammatically integrated into an isiZulu frame while also occurring near an English technical term that appears to trigger more English material. v1.5 supports that layered analysis without turning correlation into causation.

Mixed-Code Variety Mode is especially important for Tsotsitaal, Iscamtho, Kaaps, Sabela, and related named varieties. These practices cannot always be represented honestly as straightforward code-switching between two standard languages. They may involve long-standing mixed repertoires, local identity work, relexification, youth registers, urban histories, and community norms that challenge the clean Matrix Language / Embedded Language separation assumed by some models (Slabbert & Myers-Scotton, 1997; Hurst, 2008; McCormick, 2002). v1.5 therefore allows a project or span to be treated as mixed-code data, where standard-language dictionaries are resources rather than rulebooks.

Borrowing Integration Score v2 also becomes more careful. Version 1.0 could inspect noun-class assignment and concord evidence. That is valuable, but borrowing is a continuum, not a switch that flips from foreign to native once one marker appears. Some borrowed items are morphologically integrated but phonologically less adapted; others may be pronounced locally while retaining uncertain morphology. v1.5 adds optional phonological and tonal evidence where the researcher has the relevant data. It does not punish projects that only have text transcripts. It simply records which evidence was available, how it was weighted, and what remains unknown.

Finally, the Comparable Subcorpus Exporter helps Imbizo-CS data travel into wider research conversations without forcing researchers to leave their local workflow. LIDES supports structured comparison across code-switching corpora (Barnett et al., 2000), while CHAT/CLAN remains important for transcript-based interactional and child-language research communities (MacWhinney, 2000). v1.5 exports comparable subcorpora while preserving Imbizo-specific information, provenance, dictionary versions, and researcher memos. The point is not to make every project look the same. It is to let locally grounded South African research speak clearly to international formats while keeping its own analytic richness intact.

### 2. ASCII Architecture Diagram

```text
                                Researcher
                                    |
                                    v
                          gui.annotation_editor
                           |      |       |
                           |      |       +--[v1.5 NEW]--> C3 MixedCode Mode
                           |      +----------[v1.5 NEW]--> C2 Trigger Detector
                           +-----------------[v1.5 NEW]--> C1 Sister Disambiguator
                                    |
                                    v
                              core.annotation
                       MVP/v1.0 fields | v1.5 opt-in fields
                         language tags | sister_language_evidence
                         noun classes  | trigger_candidates
                         concord links | mixed_code_variety
                         4-M tags      | integration_v2_evidence
                                    |
              +---------------------+----------------------+
              |                     |                      |
              v                     v                      v
          core.lid.*          core.noun_class        core.concord
              |                     |                      |
              +--[v1.5 NEW]--> C1 Sister <---[v1.5 NEW]---+
                                    |
                                    v
                              core.four_m
                                    |
                 +------------------+-------------------+
                 |                                      |
                 v                                      v
       [v1.5 NEW] C2 Trigger                  [v1.5 NEW] C3 MixedCode
       Clyne-style candidate                  variety-aware annotation
       contexts                               defaults and warnings
                 |                                      |
                 +------------------+-------------------+
                                    |
                                    v
                         [v1.5 NEW] D1 IntegrationV2
                         morphology + concord + optional
                         phonological / tonal evidence
                                    |
                                    v
                              core.metrics
                                |      |
                                |      +--[v1.5 NEW]--> trigger summaries
                                |      +--[v1.5 NEW]--> sister-language ambiguity rates
                                |      +--[v1.5 NEW]--> integration v2 distributions
                                v
                       gui.metrics_dashboard
                                |
                                v
                              core.export
                                |
                                +--[v1.5 NEW]--> D2 Interop
                                |                 LIDES + CHAT/CLAN export
                                v
                          core.provenance
                                |
                                +--[v1.5 NEW]--> D3 CommunityReview
                                |                 offline review packets,
                                |                 dictionary comments,
                                |                 reviewer attestations
                                v
                              plugins.api
                                |
                                +--[v1.5 NEW]--> local sister-language packs
                                +--[v1.5 NEW]--> local trigger-rule packs
                                +--[v1.5 NEW]--> local mixed-code variety profiles
                                +--[v1.5 NEW]--> local interop/export adapters
```

### 3. Risk Register

| Risk | Affected Principle | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| Sister-language heuristics over-confidently labelling ambiguous tokens | Researcher interpretive authority; linguistic dignity | High | High | Store ranked evidence, ambiguity labels, and `unassigned` as first-class outcomes; never overwrite manual language tags; require provenance for accepted suggestions. |
| Trigger detection encouraging post-hoc rationalization of CS choices | Humanities-led; theoretical pluralism | Medium | High | Present triggers as candidate contexts only, with plain-language warnings that Clyne-style triggering is an analytic hypothesis, not proof of speaker motivation (Clyne, 1967, 2003). |
| Tsotsitaal mode being misapplied to ordinary CS data | Linguistic dignity; reproducibility | Medium | Medium | Make Mixed-Code Variety Mode project- or span-level and explicit; require a researcher memo when enabled; keep standard CS annotation available alongside variety labels (Slabbert & Myers-Scotton, 1997; Hurst, 2008). |
| Phonological integration scoring requiring data the user does not have | Incremental knowledge-building; low-resource design | High | Medium | Treat phonological and tonal evidence as optional fields; report "not available" rather than zero; keep v1.0 morphology/concord score reproducible. |
| LIDES / CHAT export losing v1.0-specific information | Interoperability; citability and reproducibility | Medium | High | Export a standards-compatible view plus an Imbizo sidecar JSON preserving noun-class, concord, 4-M, provenance, dictionary versions, and researcher memos (Barnett et al., 2000; MacWhinney, 2000). |
| Community review workflow creating governance asymmetries (who reviews whom?) | Decolonial computing posture; CARE-aligned governance | Medium | High | Record reviewer role, consent, community affiliation where voluntarily provided, and review scope; allow local projects to reject upstream dictionary changes; establish advisory-board review norms (Carroll et al., 2020). |
| Migration corrupting v1.0 projects with `concord_links` and `four_m_audit` data | Backward compatibility; data sovereignty | Low | High | Add only nullable v1.5 tables/columns, back up before migration, test migration against populated v1.0 projects, and verify hashes before and after migration. |
| Mixed-code profiles becoming new prescriptive standards | Theoretical pluralism; linguistic dignity | Medium | High | Mark profiles as locally reviewed resources, not authoritative grammars; allow project-local overrides and rejection notes; keep ethnographic memos visible in exports (McCormick, 2002; Mesthrie, 2008). |
