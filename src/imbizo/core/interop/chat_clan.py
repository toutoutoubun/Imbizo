"""CHAT/CLAN export for Imbizo-CS projects.

The exporter writes a conservative UTF-8 CHAT transcript for offline CHILDES /
CLAN workflows (MacWhinney, 2000). Imbizo-specific fields that lack native CHAT
tiers are preserved in `%xcom` lines prefixed with `IMBIZO-CS:` and documented
in a companion losses file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Any

from imbizo import __version__
from imbizo.core.annotation import Project, Token


@dataclass(slots=True)
class ChatExportReport:
    """Structured result from a CHAT export."""

    output_path: Path
    losses_path: Path
    utterance_count: int
    token_count: int
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ChatValidationReport:
    """Offline validation report for CHAT text."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    documented_losses: list[str] = field(default_factory=list)


def to_chat(project: Project, output_path: Path | None = None, *, utf8: bool = False) -> ChatExportReport | str:
    """Export a project to CHAT, or return text when no path is supplied."""

    text = _build_chat_text(project, utf8=utf8)
    if output_path is None:
        return text
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8" if utf8 else "ascii", errors="xmlcharrefreplace")
    losses_path = output_path.with_suffix(output_path.suffix + ".losses.txt")
    losses_path.write_text(_losses_text(), encoding="utf-8")
    tokens = _tokens(project)
    return ChatExportReport(output_path, losses_path, len(_group_tokens(tokens)), len(tokens))


def validate_chat(text: str) -> ChatValidationReport:
    """Validate CHAT structure offline; no remote CHECK service is contacted."""

    errors: list[str] = []
    warnings: list[str] = []
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0] not in {"@UTF8", "@Begin"}:
        errors.append("CHAT must begin with @UTF8 or @Begin.")
    if "@Begin" not in lines:
        errors.append("Missing @Begin marker.")
    if "@End" not in lines:
        errors.append("Missing @End marker.")
    header_order = ["@Begin", "@Languages:", "@Participants:"]
    _validate_header_order(lines, header_order, errors)
    participants = _participant_codes(lines)
    for line in lines:
        if line.startswith("*"):
            match = re.match(r"\*([A-Z0-9_]+):\t", line)
            if not match:
                errors.append(f"Malformed main tier: {line}")
            elif participants and match.group(1) not in participants:
                errors.append(f"Main tier speaker {match.group(1)} absent from @Participants.")
        elif line.startswith("%") and ":\t" not in line:
            errors.append(f"Malformed dependent tier: {line}")
    if not any(line.startswith("*") for line in lines):
        warnings.append("No main tiers found.")
    return ChatValidationReport(valid=not errors, errors=errors, warnings=warnings, documented_losses=LOSS_FIELDS.copy())


def export_chat_clan(
    tokens: list[Token],
    cha_path: Path,
    sidecar_path: Path,
    project_metadata: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible helper that writes CHAT and a small sidecar."""

    project = Project(
        id=str((project_metadata or {}).get("id", "project")),
        title=str((project_metadata or {}).get("title", "Imbizo-CS project")),
        tokens=tokens,
        metadata=project_metadata,
    )
    to_chat(project, cha_path)
    sidecar_path.write_text("{\n  \"format\": \"imbizo_chat_sidecar\"\n}\n", encoding="utf-8")


LOSS_FIELDS = [
    "4-M types represented in %xcom rather than a native CHAT tier",
    "integration scores represented in %xcom",
    "concord_links not represented as CHAT %gra dependencies",
    "mixed_code_spans flattened to comments",
    "phonological_features flattened to comments",
]


def _build_chat_text(project: Project, *, utf8: bool) -> str:
    tokens = _tokens(project)
    grouped = _group_tokens(tokens)
    languages = sorted({token.language or "und" for token in tokens}) or ["und"]
    participants = _participants(tokens)
    lines = []
    if utf8:
        lines.append("@UTF8")
    lines.extend(
        [
            "@Begin",
            f"@Languages:\t{', '.join(languages)}",
            "@Participants:\t" + ", ".join(f"{code} {name} {role}" for code, name, role in participants),
        ]
    )
    corpus = _safe_code(project.id)
    for code, _name, role in participants:
        lines.append(f"@ID:\tund|{corpus}|{code}| | | | |{role}| | |")
    metadata = getattr(project, "metadata", None) or {}
    if metadata.get("media_filename"):
        lines.append(f"@Media:\t{metadata['media_filename']}, {metadata.get('media_type', 'audio')}")
    lines.append(f"@Date:\t{datetime.now(UTC).strftime('%d-%b-%Y').upper()}")
    lines.append(f"@Situation:\t{_clean_chat(metadata.get('description', project.title), utf8=utf8)}")
    lines.append(f"@Comment:\tExported locally by Imbizo-CS Workbench {__version__}; MacWhinney (2000).")
    for utterance_id, utterance_tokens in grouped.items():
        ordered = sorted(utterance_tokens, key=lambda token: token.position)
        speaker = _chat_speaker(ordered[0].speaker_id if ordered else None)
        lines.append(f"*{speaker}:\t{_main_tier_text(ordered, utf8=utf8)}")
        mor = _mor_tier(ordered, utf8=utf8)
        if mor:
            lines.append(f"%mor:\t{mor}")
        memo = _memo_text(ordered, utf8=utf8)
        if memo:
            lines.append(f"%com:\t{memo}")
        xcom = _xcom_text(utterance_id, ordered)
        if xcom:
            lines.append(f"%ximb:\tIMBIZO-CS: {xcom}")
            lines.append(f"%xcom:\tIMBIZO-CS: {xcom}")
    lines.append("@End")
    return "\n".join(lines) + "\n"


def _main_tier_text(tokens: list[Token], *, utf8: bool) -> str:
    parts: list[str] = []
    previous_language: str | None = None
    for token in tokens:
        language = token.language or "und"
        surface = _clean_chat(token.surface, utf8=utf8)
        if previous_language and language != previous_language:
            parts.append(f"[- @{language}]")
        parts.append(surface)
        previous_language = language
    return " ".join(parts) + " ."


def _mor_tier(tokens: list[Token], *, utf8: bool) -> str:
    pieces: list[str] = []
    for token in tokens:
        tags: list[str] = []
        if token.nc_class is not None:
            tags.append(f"NC{token.nc_class}")
        if token.nc_prefix:
            tags.append(f"PFX={token.nc_prefix}")
        if token.four_m_type:
            tags.append(f"4M={token.four_m_type}")
        if tags:
            pieces.append(f"{_clean_chat(token.surface, utf8=utf8)}|{'/'.join(tags)}")
    return " ".join(pieces)


def _xcom_text(utterance_id: str, tokens: list[Token]) -> str:
    fragments = [f"utterance={utterance_id}"]
    for token in tokens:
        extras: list[str] = []
        if token.trigger_role:
            extras.append(f"trigger={token.trigger_role}")
        if token.mixed_code_variety:
            extras.append(f"mixed_code={token.mixed_code_variety}")
        if token.phon_integration_score is not None:
            extras.append(f"integration_v2={token.phon_integration_score:.3f}")
        if extras:
            fragments.append(f"{token.id}({';'.join(extras)})")
    return " ".join(fragments)


def _memo_text(tokens: list[Token], *, utf8: bool) -> str:
    memos = [_clean_chat((token.metadata or {}).get("memo", ""), utf8=utf8) for token in tokens]
    return " | ".join(memo for memo in memos if memo)


def _losses_text() -> str:
    lines = ["# Imbizo-CS to CHAT documented losses", "Reference: MacWhinney (2000).", ""]
    for field in LOSS_FIELDS:
        lines.append(f"- {field}: retained in %xcom or documented here because CHAT has no direct native field.")
    return "\n".join(lines) + "\n"


def _tokens(project: Project) -> list[Token]:
    return list(getattr(project, "tokens", []))


def _group_tokens(tokens: list[Token]) -> dict[str, list[Token]]:
    grouped: dict[str, list[Token]] = {}
    for token in tokens:
        grouped.setdefault(token.utterance_id or "utt_unknown", []).append(token)
    return dict(sorted(grouped.items()))


def _participants(tokens: list[Token]) -> list[tuple[str, str, str]]:
    speakers = sorted({token.speaker_id for token in tokens if token.speaker_id}) or ["SP01"]
    return [(_chat_speaker(speaker), _chat_speaker(speaker), "Participant") for speaker in speakers]


def _participant_codes(lines: list[str]) -> set[str]:
    participants: set[str] = set()
    for line in lines:
        if line.startswith("@Participants:\t"):
            body = line.split("\t", 1)[1]
            for item in body.split(","):
                code = item.strip().split(" ", 1)[0]
                if code:
                    participants.add(code)
    return participants


def _validate_header_order(lines: list[str], prefixes: list[str], errors: list[str]) -> None:
    positions: list[int] = []
    for prefix in prefixes:
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                positions.append(index)
                break
        else:
            errors.append(f"Missing CHAT header {prefix}")
    if positions != sorted(positions):
        errors.append("CHAT headers are not in the expected order.")


def _chat_speaker(speaker_id: str | None) -> str:
    cleaned = "".join(char for char in (speaker_id or "SP01").upper() if char.isalnum() or char == "_")
    if not cleaned.startswith("SP") and len(cleaned) < 3:
        cleaned = f"SP{cleaned}"
    return cleaned[:8] or "SP01"


def _safe_code(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum() or char in {"_", "-"}) or "imbizo"


def _clean_chat(value: Any, *, utf8: bool = True) -> str:
    cleaned = str(value).replace("\t", " ").replace("\n", " ").strip()
    if utf8:
        return cleaned
    return cleaned.encode("ascii", errors="xmlcharrefreplace").decode("ascii")
