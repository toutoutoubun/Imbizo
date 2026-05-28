# Licence Compatibility Audit

This note is a release-engineering audit, not legal advice. It records how the
Imbizo-CS Workbench source licence and bundled/bootstrapped resource licences
fit together as of v1.5.0.

## Sources Checked

- Root package metadata: `pyproject.toml`, `CITATION.cff`, `LICENSE`,
  `README.md`, `PRINCIPLES.md`.
- Resource manifests: `bootstrap/sources.yaml`, `LICENSES/INDEX.md`,
  `LICENSES/README.md`.
- Enforcement paths: `tools/bootstrap.py`, `tools/make_bundle.py`,
  `tools/check_compliance.py`, `scripts/release_check.py`.
- Primary references:
  - GNU Affero General Public License v3, Free Software Foundation:
    https://www.gnu.org/licenses/agpl-3.0.html
  - GNU license compatibility list, Free Software Foundation:
    https://www.gnu.org/licenses/license-list.html
  - Creative Commons compatible licences list:
    https://creativecommons.org/compatible-licenses/
  - Creative Commons FAQ on NonCommercial:
    https://creativecommons.org/faq/

## Software Licence

Decision: **AGPL-3.0-or-later**.

Status after this audit: **consistent**.

- `pyproject.toml` declares `AGPL-3.0-or-later`.
- `CITATION.cff` declares `AGPL-3.0-or-later`.
- `PRINCIPLES.md` Part IV explains why AGPLv3 was chosen.
- `LICENSE` now contains the official FSF AGPLv3 text.
- `scripts/release_check.py` now fails if `LICENSE` no longer contains AGPLv3
  text or if stale GPL-only wording returns.

The prior repository state had a material inconsistency: the root `LICENSE`
file described GPLv3-or-later while the rest of the project had moved to
AGPLv3. That is now fixed.

## Runtime Dependencies

The mandatory Python dependencies are permissive or widely used open-source
packages. No mandatory dependency was found that obviously conflicts with
AGPLv3 source distribution:

| Dependency | Licence class | Audit note |
| --- | --- | --- |
| `click` | BSD-style | Permissive. |
| `pydantic` | MIT | Permissive. |
| `PyYAML` | MIT | Permissive. |
| `matplotlib` | Matplotlib licence | Permissive attribution-style terms. |
| `pandas` | BSD-3-Clause | Permissive. |
| `lxml` | BSD-3-Clause | Permissive. |

Optional dependencies should remain optional in release notes and offline
wheelhouses. `PySide6` is LGPL/commercial upstream; Imbizo-CS uses it as an
optional dynamically linked GUI dependency and does not vendor Qt binaries in
the Python wheel. Standalone PyInstaller builds need a separate Qt/LGPL
redistribution pass before publication.

## Resource Tier Audit

The tiering model remains the right structure:

- **Tier 1 Core**: no commercial-use restriction; may be installed by default.
- **Tier 2 Optional-NC / aggregation-only**: explicit opt-in and environment
  acknowledgement required.
- **Tier 3 Community**: not silently auto-installed; routed through community
  review or explicit community acknowledgement.

| Resource | Manifest status | Compatibility conclusion |
| --- | --- | --- |
| UP Multilingual Lexicons | `CC-BY-4.0`, Tier 1, metadata probe required | Acceptable as attributed resource data once source metadata confirms CC-BY-4.0. |
| African Wordnet | CC-BY-4.0 only when SADiLaR metadata allows | Correctly conservative; files without allowed rights are skipped. |
| UNISA Termbank | `PER-FILE-SADILAR-METADATA` | Correct: no blanket licence is assumed; the adapter currently converts only per-file `CC-BY-4.0` rights and skips generic OER / unclear / NC rights. |
| EXDN | Public-domain historical source | Acceptable with provenance/citation caution; jurisdiction-specific review still recommended for public release bundles. |
| NCHLT Text Corpora | `CC-BY-2.5-SA`, Tier 1 aggregation | Acceptable as attribution corpus aggregation; note that `SA` here means South Africa, not ShareAlike. |
| JOHD morph corpora | CC-BY-4.0 when verified | Acceptable after handle/file rights verification. |
| ZA_LEX | Apache/MIT scripts plus per-language licence files | Acceptable only when upstream per-language `LICENCE` files are preserved. |
| whisper.cpp source | MIT, opt-in ASR | Source licence compatible; model files remain out of scope until separately audited. |
| fastText lid.176 | `CC-BY-SA-3.0`, Tier 2 | Correctly aggregation-only. CC lists GPLv3 compatibility for BY-SA 4.0, but no non-CC compatible licence for BY-SA 3.0. |
| MasakhaPOS / MasakhaNER | `CC-BY-NC-4.0`, Tier 2 | Correctly opt-in only; NC obligations must propagate to shared tagged data and reports. |
| Mafoko / za-mavito | mixed NOODL / CC-BY-NC-SA-2.5-ZA, Tier 3 | Correctly not default Core data; row-level audit needed before finer redistribution. |

## Enforcement Changes Made In This Audit

1. Replaced the root `LICENSE` with official AGPLv3 text.
2. Extended `scripts/release_check.py` so the release check verifies the root
   software licence text matches AGPLv3.
3. Extended `tools/bootstrap.py` and `tools/make_bundle.py` so resource
   bootstrap/bundle creation refuses placeholder licence files.
4. Added a regression test proving placeholder licence files are rejected before
   bundle/resource publication.
5. Clarified `LICENSES/README.md` and `docs/release_packaging.md`: placeholders
   may exist as source-tree audit reminders, but not in shipped resource
   bundles or converted imported dictionaries.

## Remaining Release Blockers

These are not blockers for the AGPLv3 Python package itself, but they are
blockers for a resource bundle that contains the corresponding resource:

- `LICENSES/OER-UNISA.txt` is retained only as a historical marker because the
  UNISA / SADiLaR termbank does not have one blanket OER licence. New converted
  files should use concrete per-file rights such as `CC-BY-4.0`; generic OER
  statements are skipped unless project governance later adds a concrete
  redistributable licence text.
- PyInstaller desktop bundles need an additional dependency-notice inventory,
  especially for Qt/PySide6.
- Built-in starter dictionaries are project-authored YAML derived from
  reference grammars and should remain marked unverified. Avoid copying
  protected prose or tables from grammar books into those files.
