"""CHAT/CLAN-compatible export.

The exporter writes a conservative CHAT transcript plus Imbizo metadata comments
for offline use. Validation is local only; no remote CHAT checker is contacted
(MacWhinney, 2000).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from ..annotation import Project, Token


@dataclass(slots=True)
class ChatValidationReport:
    """Offline validation report for CHAT text."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    documented_losses: list[str] = field(default_factory=list)


def to_chat(project: Project) -> str:
    """Return a CHAT-format transcript string for CLAN-oriented workflows."""

    utterances: dict[str, list[Token]] = {}
    for token in project.tokens:
        utterances.setdefault(token.utterance_id or "utt_unknown", []).append(token)
    lines = [
        "@UTF8",
        "@Begin",
        f"@Languages:\t{_languages(project.tokens)}",
        f"@Participants:\t{_participants(project.tokens)}",
        f"@ID:\timbizo|{project.id}|{project.title}|",
        "@Comment:\tExported locally by Imbizo-CS; v1.5 fields are preserved in %ximb tiers.",
    ]
    for index, (utterance_id, group) in enumerate(sorted(utterances.items()), start=1):
        speaker = _chat_speaker(group[0].speaker_id, index)
        words = " ".join(token.surface for token in sorted(group, key=lambda item: item.position))
        lines.append(f"*{speaker}:\t{words} .")
        ximb = {
            "utterance_id": utterance_id,
            "tokens": [_token_sidecar(token) for token in sorted(group, key=lambda item: item.position)],
        }
        lines.append("%ximb:\t" + json.dumps(ximb, ensure_ascii=True, sort_keys=True))
    lines.append("@End")
    return "\n".join(lines) + "\n"


def validate_chat(text: str) -> ChatValidationReport:
    """Run an offline schema check for the Imbizo CHAT export."""

    errors: list[str] = []
    warnings: list[str] = []
    losses = [
        "CHAT does not natively encode all Imbizo noun-class, concord, 4-M, or v1.5 fields.",
        "Imbizo-specific data is stored in local %ximb tiers and should be kept with the transcript.",
    ]
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "@UTF8":
        errors.append("Missing @UTF8 header.")
    if "@Begin" not in lines:
        errors.append("Missing @Begin marker.")
    if "@End" not in lines:
        errors.append("Missing @End marker.")
    main_tiers = [line for line in lines if line.startswith("*")]
    if not main_tiers:
        errors.append("No participant tiers found.")
    for line in main_tiers:
        if ":\t" not in line:
            errors.append(f"Malformed participant tier: {line}")
    for line in [line for line in lines if line.startswith("%ximb:\t")]:
        try:
            json.loads(line.split("\t", 1)[1])
        except json.JSONDecodeError as exc:
            errors.append(f"Malformed %ximb JSON: {exc}")
    if len([line for line in lines if line.startswith("%ximb:\t")]) < len(main_tiers):
        warnings.append("Some participant tiers lack Imbizo %ximb metadata.")
    return ChatValidationReport(valid=not errors, errors=errors, warnings=warnings, documented_losses=losses)


def export_chat_clan(
    tokens: list[Token],
    cha_path: Path,
    sidecar_path: Path,
    project_metadata: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible helper that writes CHAT plus a JSON sidecar file."""

    project = Project(
        id=str((project_metadata or {}).get("id", "project")),
        title=str((project_metadata or {}).get("title", "Imbizo-CS project")),
        tokens=tokens,
        metadata=project_metadata,
    )
    text = to_chat(project)
    cha_path.parent.mkdir(parents=True, exist_ok=True)
    cha_path.write_text(text, encoding="utf-8")
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
    speakers = sorted({_chat_speaker(token.speaker_id, index + 1) for index, token in enumerate(tokens) if token.speaker_id})
    return ", ".join(f"{speaker} Participant" for speaker in speakers) if speakers else "SP01 Participant"


def _chat_speaker(speaker_id: str | None, fallback_index: int) -> str:
    if not speaker_id:
        return f"SP{fallback_index:02d}"
    cleaned = "".join(char for char in speaker_id.upper() if char.isalnum())
    return (cleaned or f"SP{fallback_index:02d}")[:8]


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
