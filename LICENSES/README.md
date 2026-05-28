# Dictionary Bootstrap Licenses

This directory stores the license text shipped with imported dictionary and
processing-resource sources. `INDEX.md` is the authoritative compatibility
index: it separates the Imbizo-CS software licence (AGPLv3) from resource
licences and records the Core / Optional-NC / Community tier model.

- `CC-BY-4.0.txt`: University of Pretoria lexicons and allowed African Wordnet files that declare CC-BY-4.0.
- `CC-BY-NC-SA-2.5-ZA.txt`: Mafoko files that declare Creative Commons Attribution-NonCommercial-ShareAlike 2.5 South Africa.
- `NWULITE-OBODO-1.0.txt`: Mafoko files that declare the Nwulite Obodo Open Data License.
- `PUBLIC-DOMAIN.txt`: EXDN historical medical dictionary source.
- `OER-UNISA.txt`: UNISA / SADiLaR termbank files only when the XML rights metadata explicitly declares OER.
- `CC-BY-2.5-SA.txt`: `nchlt_text_corpora`.
- `CC-BY-SA-3.0.txt`: `fasttext_lid176_ftz`, `fasttext_lid176_bin_optional`.
- `CC-BY-NC-4.0.txt`: `masakhapos`, `masakhaner`.
- `MIT.txt`: `whisper_cpp_optional` source and model license, where applicable.
- `APACHE-2.0.txt`: Masakhane code and ZA_LEX scripts when upstream declares Apache-2.0.

Resource-to-primary-license index:

| Resource id | License file |
| --- | --- |
| `up_multilingual_lexicons` | `CC-BY-4.0.txt` |
| `mafoko` | `NWULITE-OBODO-1.0.txt` |
| `african_wordnet` | `CC-BY-4.0.txt` |
| `unisa_termbank` | Per-file SADiLaR XML metadata; converted outputs point to `CC-BY-4.0.txt` or `OER-UNISA.txt` when verified, and unknown / NC files are skipped by default. |
| `exdn` | `PUBLIC-DOMAIN.txt` |
| `fasttext_lid176_ftz` | `CC-BY-SA-3.0.txt` |
| `fasttext_lid176_bin_optional` | `CC-BY-SA-3.0.txt` |
| `nchlt_text_corpora` | `CC-BY-2.5-SA.txt` |
| `morph_annotated_corpora` | `CC-BY-4.0.txt` when SADiLaR metadata confirms CC-BY-4.0 |
| `masakhapos` | `CC-BY-NC-4.0.txt` |
| `masakhaner` | `CC-BY-NC-4.0.txt` |
| `za_lex` | `APACHE-2.0.txt` |
| `whisper_cpp_optional` | `MIT.txt` |

Some upstream bundles carry per-file or per-language license declarations. The
primary license file above is the compliance anchor except for metadata-gated
sources such as `unisa_termbank`, where the adapter must read each XML file's
rights statement and write the resolved licence into the converted YAML.

Files containing `REPLACE THIS FILE WITH THE VERBATIM LICENSE TEXT` are deliberate placeholders. `tools/check_compliance.py` fails if imported dictionaries are shipped while a matching license file remains a placeholder.
