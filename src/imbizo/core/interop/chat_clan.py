"""CHAT/CLAN-compatible transcript export.

The CHAT text output keeps utterance text readable for CLAN workflows while a
JSON sidecar preserves Imbizo-specific annotation fields that CHAT cannot
represent directly (MacWhinney, 2000).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..annotation import Token


def export_chat_clan(
    tokens: list[Token],
    cha_path: Path,
    sidecar_path: Path,
    project_metadata: dict[str, Any] | None = None,
) -> None:
    """Export a simple CHAT file and an Imbizo JSON sidecar."""

    utterances: dict[str, list[Token]] = {}
    for token in tokens:
        utterances.setdefault(token.utterance_id or "utt_unknown", []).append(token)

    lines = [
        "@UTF8",
        "@Begin",
        f"@Languages:\t{_languages(tokens)}",
        f"@Participants:\t{_participants(tokens)}",
        f"@Comment:\tExported by Imbizo-CS for CHAT/CLAN compatibility; see sidecar for v1.5 fields.",
    ]
    for index, (utterance_id, group) in enumerate(sorted(utterances.items()), start=1):
        speaker = group[0].speaker_id or f"SP{index:02d}"
        words = " ".join(token.surface for token in sorted(group, key=lambda item: item.position))
        lines.append(f"*{speaker}:\t{words} .")
        lines.append(f"%ximb:\tutterance_id={utterance_id}")
    lines.append("@End")

    cha_path.parent.mkdir(parents=True, exist_ok=True)
    cha_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    sidecar = {
        "format": "imbizo_chat_sidecar",
        "chat_reference": "MacWhinney (2000)",
        "project": project_metadata or {},
        "tokens": [_token_sidecar(token) for token in tokens],
    }
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")


def _languages(tokens: list[Token]) -> str:
    languages = sorted({token.language for token in tokens if token.language})
    return ", ".join(languages) if languages else "und"


def _participants(tokens: list[Token]) -> str:
    speakers = sorted({token.speaker_id for token in tokens if token.speaker_id})
    return ", ".join(f"{speaker} Participant" for speaker in speakers) if speakers else "SP01 Participant"


def _token_sidecar(token: Token) -> dict[str, Any]:
    return {
        "id": token.id,
        "utterance_id": token.utterance_id,
        "position": token.position,
        "surface": token.surface,
        "language": token.language,
        "nc_class": token.nc_class,
        "four_m_type": token.four_m_type,
        "sister_lang_confidence": token.sister_lang_confidence,
        "sister_lang_evidence": token.sister_lang_evidence,
        "trigger_role": token.trigger_role,
        "mixed_code_variety": token.mixed_code_variety,
        "phon_integration_score": token.phon_integration_score,
    }
