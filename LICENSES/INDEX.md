# Licence Index

This index separates the **software licence** for Imbizo-CS source code from
the **resource licences** carried by dictionaries, models, corpora, and
processing resources. See `PRINCIPLES.md`, Part IV: Licence philosophy.

## Software licence

**AGPLv3** is the licence under which Imbizo-CS source code is distributed. If
users modify and redistribute the software, or run a modified network-accessible
version, they must preserve the corresponding source freedoms required by the
AGPLv3. This does not automatically relicense independently obtained research
data, corpora, dictionaries, or model files.

## Resource licences

Resource licences govern the imported files under `dictionaries/imported/`,
`models/`, `corpora/`, and `processing/`. Imbizo-CS records whether each resource
is a combination, an aggregation-only resource, or a community-governed overlay.

## Tier-1 resource licences

| SPDX id | Full text file | Resources | AGPLv3 compatibility note |
| --- | --- | --- | --- |
| `CC-BY-4.0` | `LICENSES/CC-BY-4.0.txt` | `up_multilingual_lexicons`, `african_wordnet`, `morph_annotated_corpora` when verified | Compatible for Imbizo-CS resource use with attribution preserved. |
| `PER-FILE-SADILAR-METADATA` | not a licence text; see the concrete licence files named in each converted YAML | `unisa_termbank` manifest entry before conversion | The source is metadata-gated. The adapter converts only files whose rights metadata resolves to the Tier-1 allow-list, currently `CC-BY-4.0`, and skips generic OER, unclear, NC, or incompatible statements. |
| `Public-Domain` | `LICENSES/PUBLIC-DOMAIN.txt` | `exdn` | No copyright restriction asserted; citation remains a provenance norm. |
| `CC-BY-2.5-SA` | `LICENSES/CC-BY-2.5-SA.txt` | `nchlt_text_corpora` | Aggregation-only corpus resource; attribution required. Here `SA` means South Africa, not ShareAlike. |
| `Apache-2.0-OR-MIT` | `LICENSES/APACHE-2.0.txt`, `LICENSES/MIT.txt` | `za_lex` | Permissive software/resource scripts; per-language data licence files must remain attached. |
| `MIT` | `LICENSES/MIT.txt` | `whisper_cpp_optional` source | Compatible source licence, but ASR remains explicit opt-in and models require separate review. |

## Tier-2 resource licences

Tier-2 resources are opt-in and require `--include-nc-data` plus
`IMBIZO_NC_ACCEPTED=1` at bootstrap time. They are not hidden inside the default
AGPLv3 application because their obligations can constrain downstream reuse.

| SPDX id | Full text file | Resources | AGPLv3 compatibility note | Sample redistribution notice |
| --- | --- | --- | --- | --- |
| `CC-BY-NC-4.0` | `LICENSES/CC-BY-NC-4.0.txt` | `masakhapos`, `masakhaner` | Aggregation-only with AGPLv3; commercial reuse of derived data outputs may be restricted. | Preserve attribution and NonCommercial notice in reports and redistributed tagged data. |
| `CC-BY-SA-3.0` | `LICENSES/CC-BY-SA-3.0.txt` | `fasttext_lid176_ftz`, `fasttext_lid176_bin_optional` | Aggregation-only. CC-BY-SA-3.0 is not treated as AGPLv3-combinable source. | Redistributing the model or adapted model requires attribution and ShareAlike terms. |

## Tier-3 resource licences

Tier-3 is reserved for NOODL and similar community-governed licences. These
resources are not automatically downloaded by default. They travel through
community-review packets so consent, attribution, disagreement, and local
governance can be preserved.

| SPDX id | Full text file | Resources | AGPLv3 compatibility note |
| --- | --- | --- | --- |
| `MIXED-NOODL-1.0-OR-CC-BY-NC-SA-2.5-ZA` | `LICENSES/NWULITE-OBODO-1.0.txt`, `LICENSES/CC-BY-NC-SA-2.5-ZA.txt` | `mafoko` until row-level licence audit separates subsets | Community-governed or NC-SA aggregation only; never silently bundled as default Core data. |

Tier-3 placement is a design refusal: Imbizo-CS will not make sovereignty-aware
or community-conditioned data look like ordinary package data simply because a
download URL exists.
