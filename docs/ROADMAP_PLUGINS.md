# Roadmap: Optional Plugins

All plug-ins in this roadmap must remain optional. Core project creation,
annotation, metrics, provenance, and export must continue to work with every
plug-in disabled.

| Priority | Plug-in | Dependency footprint | Offline feasibility | Ethical review needed | Must remain optional |
| --- | --- | --- | --- | --- | --- |
| 1 | Local ASR with Whisper.cpp | Medium to heavy CPU model files; no GPU required if small models are selected. | Feasible through local binaries and transferred model files. | Yes, because transcript errors can affect participant representation. | Yes. Manual transcription remains the default. |
| 1 | Local ASR with Vosk | Medium; model files vary by language and accuracy. | Feasible through local wheels and model folders. | Yes, especially for low-resource language error rates. | Yes. |
| 2 | Local ASR with Coqui STT | Medium to heavy; model availability varies. | Feasible if compatible local models are packaged. | Yes, because model coverage may be uneven. | Yes. |
| 2 | AfroLID enhancement | Heavy relative to fastText; transformer runtime and local weights. | Feasible as a transferred local model bundle. | Yes, because language labels may carry identity and political meaning. | Yes. The app must work without it. |
| 2 | SADiLaR morphology resources | Light to medium dictionaries or analyzers, depending on language. | Feasible with local resource folders. | Yes, because morpheme suggestions must not overwrite local linguistic judgement. | Yes. |
| 3 | Additional languages | Light metadata, colors, dictionaries, and optional resources. | Feasible through local language packs. | Usually yes, with community review for names, autonyms, and categories. | Yes. User-defined labels stay supported. |
| 3 | Localized UI | Light translation catalogs. | Fully feasible. | Recommended, especially for community-facing terminology. | Yes per language, but the i18n system is core. |
| 4 | Optional LLM assistance | Heavy local models or explicitly consented external tools. | Local-only models are feasible but resource intensive; network tools are disabled by default. | Required. Must pass PRINCIPLES.md and project consent constraints. | Yes. Never a core dependency. |

## Local ASR

Candidate engines: Whisper.cpp, Vosk, and Coqui STT. These may create draft
transcripts, but the researcher remains the editor. No cloud transcription is
allowed by default, and any output is imported as ordinary editable transcript
segments.

## AfroLID

The AfroLID plug-in may rescore African-language or unknown predictions after
the lightweight baseline LID stage (Adebara et al., 2022). It must not download
weights silently and must preserve all labels as automatic suggestions.

## Morphology

Future morphology plug-ins may use SADiLaR resources or language-specific
analyzers. They can suggest morpheme boundaries, but manual morpheme splits
remain authoritative because Bantu morphology is analytically central to many
code-switching questions.

## Additional Languages

Post-MVP language packs should include Sepedi, siSwati, Xitsonga, Tshivenda,
and isiNdebele. Language packs are local files, not remote services, and must
coexist with user-defined varieties such as Tsotsitaal, Iscamtho, Kaaps, and
Sabela.

## Localized UI

Afrikaans, isiZulu, isiXhosa, Sesotho, and Setswana UI catalogs should be
reviewed with speakers and researchers. Translation files live under
`src/imbizo/resources/i18n/`.

## Optional LLM Assistance

LLM assistance is not part of the MVP and may only appear as an explicit,
opt-in plug-in for carefully bounded tasks such as synthetic test-data
augmentation. It must never interpret participant meaning on behalf of the
researcher, and it must never bypass consent or data-sovereignty controls.
