"""LIDES-oriented comparable subcorpus export.

The exporter writes a conservative JSON representation that keeps Imbizo v1.5
fields in a sidecar-friendly structure while supporting comparison with LIDES
code-switching conventions (Barnett et al., 2000). It does not discard local
provenance or researcher memos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..annotation import Token


def export_lides_json(
    tokens: list[Token],
    out_path: Path,
    project_metadata: dict[str, Any] | None = None,
    sidecar: dict[str, Any] | None = None,
) -> None:
    """Export tokens to a LIDES-oriented JSON file with Imbizo sidecar fields."""

    utterances: dict[str, list[Token]] = {}
    for token in tokens:
        utterances.setdefault(token.utterance_id or "unknown", []).append(token)

    payload = {
        "format": "imbizo_lides_json",
        "lides_reference": "Barnett et al. (2000)",
        "project": project_metadata or {},
        "utterances": [
            {
                "id": utterance_id,
                "tokens": [_token_to_lides(token) for token in sorted(group, key=lambda item: item.position)],
            }
            for utterance_id, group in sorted(utterances.items())
        ],
        "imbizo_sidecar": sidecar or {},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")


def _token_to_lides(token: Token) -> dict[str, Any]:
    return {
        "token_id": token.id,
        "surface": token.surface,
        "language": token.language,
        "position": token.position,
        "speaker_id": token.speaker_id,
        "imbizo_v1_0": {
            "nc_class": token.nc_class,
            "nc_prefix": token.nc_prefix,
            "four_m_type": token.four_m_type,
        },
        "imbizo_v1_5": {
            "sister_lang_confidence": token.sister_lang_confidence,
            "sister_lang_evidence": token.sister_lang_evidence,
            "trigger_role": token.trigger_role,
            "mixed_code_variety": token.mixed_code_variety,
            "phon_integration_score": token.phon_integration_score,
        },
    }
