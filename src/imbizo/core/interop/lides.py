"""LIDES Coding Manual oriented plain-text export.

The exporter maps Imbizo-CS annotations to a conservative Language Interaction
Data Exchange System text representation for comparable code-switching work
(Barnett et al., 2000). LIDES cannot represent every Imbizo-CS v1.0/v1.5 field,
so every export writes a companion `.losses.txt` explaining what was flattened
and why that matters under `PRINCIPLES.md` Part II.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from imbizo import __version__
from imbizo.core.annotation import Project, Token


@dataclass(slots=True)
class LidesExportReport:
    """Structured result from a LIDES export."""

    output_path: Path
    losses_path: Path
    utterance_count: int
    token_count: int
    languages: list[str]
    lost_fields: list[str]


@dataclass(slots=True)
class ValidationReport:
    """Offline validation report for a LIDES export."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    documented_losses: list[str] = field(default_factory=list)


def to_lides(project: Project, output_path: Path | None = None) -> LidesExportReport | str:
    """Export a project to LIDES text, or return text when no path is supplied."""

    text, lost_fields = _build_lides_text(project)
    if output_path is None:
        return text
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    losses_path = output_path.with_suffix(output_path.suffix + ".losses.txt")
    losses_path.write_text(_losses_text(lost_fields), encoding="utf-8")
    tokens = _tokens(project)
    return LidesExportReport(
        output_path=output_path,
        losses_path=losses_path,
        utterance_count=len(_group_tokens(tokens)),
        token_count=len(tokens),
        languages=sorted({token.language or "und" for token in tokens}),
        lost_fields=lost_fields,
    )


def validate_lides(text: str) -> ValidationReport:
    """Validate LIDES structure offline; no remote checker is contacted."""

    errors: list[str] = []
    warnings: list[str] = []
    required = ["LIDES VERSION:", "EXPORTED-BY:", "EXPORT-DATE:", "PROJECT-NAME:", "PROJECT-LANGUAGES:"]
    for prefix in required:
        if not any(line.startswith(prefix) for line in text.splitlines()):
            errors.append(f"Missing LIDES header line starting with {prefix}")
    speaker_codes: set[str] = set()
    for line in text.splitlines():
        if line.startswith("UTT\t"):
            parts = line.split("\t")
            if len(parts) < 5:
                errors.append(f"Malformed utterance line: {line}")
            else:
                speaker_codes.add(parts[2])
        elif line.startswith("TOK\t"):
            parts = line.split("\t")
            if len(parts) < 7:
                errors.append(f"Malformed token line: {line}")
                continue
            if not re.fullmatch(r"[a-z]{2,3}|und|mixed|borrowing|proper_noun", parts[5]):
                warnings.append(f"Non-standard language tag {parts[5]!r} on token {parts[1]}")
    if "--- DATA ---" not in text:
        errors.append("Missing --- DATA --- separator.")
    if not speaker_codes:
        warnings.append("No speaker-coded utterances found.")
    return ValidationReport(valid=not errors, errors=errors, warnings=warnings, documented_losses=LOSS_FIELDS.copy())


def parse_lides(text: str) -> list[dict[str, str]]:
    """Parse the conservative TOK records back into dictionaries for tests."""

    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("TOK\t"):
            _, token_id, utterance_id, position, surface, language, morphology = line.split("\t", 6)
            rows.append(
                {
                    "token_id": token_id,
                    "utterance_id": utterance_id,
                    "position": position,
                    "surface": surface,
                    "language": language,
                    "morphology": morphology,
                }
            )
    return rows


def export_lides_json(
    tokens: list[Token],
    out_path: Path,
    project_metadata: dict[str, Any] | None = None,
    sidecar: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible helper retained for older scripts."""

    project = Project(
        id=str((project_metadata or {}).get("id", "project")),
        title=str((project_metadata or {}).get("title", "Imbizo-CS project")),
        tokens=tokens,
        metadata={**(project_metadata or {}), "sidecar": sidecar or {}},
    )
    result = to_lides(project, out_path)
    if isinstance(result, str):
        out_path.write_text(result, encoding="utf-8")


LOSS_FIELDS = [
    "four_m_type beyond LIDES vocabulary",
    "concord_links",
    "mixed_code_spans",
    "trigger_links",
    "phonological_features",
    "integration_score weights",
    "community review status",
]


def _build_lides_text(project: Project) -> tuple[str, list[str]]:
    tokens = _tokens(project)
    grouped = _group_tokens(tokens)
    languages = sorted({token.language or "und" for token in tokens}) or ["und"]
    lines = [
        "LIDES VERSION: 1.0",
        f"EXPORTED-BY: Imbizo-CS Workbench {__version__}",
        f"EXPORT-DATE: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"PROJECT-NAME: {project.title}",
        f"PROJECT-LANGUAGES: {', '.join(languages)}",
        f"IMBIZO-CS-PROJECT-HASH: {_project_hash(project)}",
        "REFERENCE: Barnett et al. (2000)",
        "--- DATA ---",
    ]
    for utterance_id, utterance_tokens in grouped.items():
        ordered = sorted(utterance_tokens, key=lambda token: token.position)
        speaker = _speaker_code(ordered[0].speaker_id if ordered else None)
        raw = " ".join(token.surface for token in ordered)
        lines.append(f"UTT\t{utterance_id}\t{speaker}\t{_start_time(ordered)}\t{raw}")
        for token in ordered:
            language = token.language or "und"
            morphology = _morphology_tag(token)
            lines.append(f"TOK\t{token.id}\t{utterance_id}\t{token.position}\t{_clean_field(token.surface)}\t{language}\t{morphology}")
            lines.append(f"LID\t{token.id}\t@{_lides_language(language)}")
            lines.append(f"XIMB\t{token.id}\t{json.dumps(_imbizo_sidecar(token), ensure_ascii=True, sort_keys=True)}")
    lines.append("--- END DATA ---")
    return "\n".join(lines) + "\n", LOSS_FIELDS.copy()


def _losses_text(lost_fields: list[str]) -> str:
    lines = [
        "# Imbizo-CS to LIDES documented losses",
        "Reference: Barnett et al. (2000).",
        "These losses matter because PRINCIPLES.md Part II explains why morphology matters for Bantu-language code-switching.",
        "",
    ]
    for field in lost_fields:
        lines.append(f"- {field}: not natively representable in this conservative LIDES plain-text export; see PRINCIPLES.md Part II.")
    return "\n".join(lines) + "\n"


def _tokens(project: Project) -> list[Token]:
    return list(getattr(project, "tokens", []))


def _group_tokens(tokens: list[Token]) -> dict[str, list[Token]]:
    grouped: dict[str, list[Token]] = {}
    for token in tokens:
        grouped.setdefault(token.utterance_id or "utt_unknown", []).append(token)
    return dict(sorted(grouped.items()))


def _morphology_tag(token: Token) -> str:
    parts: list[str] = []
    if token.nc_class is not None:
        parts.append(f"NC={token.nc_class}")
    if token.nc_prefix:
        parts.append(f"PFX={token.nc_prefix}")
    if token.four_m_type:
        parts.append(f"4M={token.four_m_type}")
    return "+".join(parts) if parts else "_"


def _imbizo_sidecar(token: Token) -> dict[str, Any]:
    return {
        "four_m_type": token.four_m_type,
        "mixed_code_variety": token.mixed_code_variety,
        "nc_class": token.nc_class,
        "phon_integration_score": token.phon_integration_score,
        "sister_lang_confidence": token.sister_lang_confidence,
        "sister_lang_evidence": token.sister_lang_evidence,
        "trigger_role": token.trigger_role,
    }


def _project_hash(project: Project) -> str:
    metadata = getattr(project, "metadata", None) or {}
    database = metadata.get("database_path") or (Path(project.project_path) / "project.sqlite" if getattr(project, "project_path", None) else None)
    if database and Path(database).exists():
        return sha256(Path(database).read_bytes()).hexdigest()
    payload = "\n".join(f"{token.id}:{token.surface}:{token.language}" for token in _tokens(project))
    return sha256(payload.encode("utf-8")).hexdigest()


def _speaker_code(value: str | None) -> str:
    cleaned = "".join(char for char in (value or "SPK").upper() if char.isalnum())
    return cleaned[:10] or "SPK"


def _start_time(tokens: list[Token]) -> str:
    for token in tokens:
        if token.metadata and token.metadata.get("start_time_ms") is not None:
            return str(token.metadata["start_time_ms"])
    return ""


def _lides_language(language: str) -> str:
    mapping = {"eng": "en", "zul": "zu", "xho": "xh", "afr": "af", "sot": "st", "tsn": "tn"}
    return mapping.get(language, language)


def _clean_field(value: str) -> str:
    return value.replace("\t", " ").replace("\n", " ").strip()
