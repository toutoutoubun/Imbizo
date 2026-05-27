"""LIDES-oriented export for comparable code-switching subcorpora.

The exporter maps Imbizo-CS annotations to a conservative line-oriented format
inspired by the LIDES coding tradition (Barnett et al., 2000). Round-trip is
not guaranteed because Imbizo v1.0/v1.5 fields are richer than the shared
comparison view; validation reports documented losses explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from ..annotation import Project, Token


@dataclass(slots=True)
class ValidationReport:
    """Offline validation report for a LIDES-oriented export."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    documented_losses: list[str] = field(default_factory=list)


def to_lides(project: Project) -> str:
    """Return a LIDES-oriented text export from Imbizo-CS annotations.

    The output is intentionally plain and local. It includes a JSON sidecar
    line for Imbizo-specific fields so LIDES comparison does not erase v1.0
    noun-class, concord, 4-M, or v1.5 trigger/mixed-code evidence.
    """

    lines = [
        "# IMBIZO_LIDES 1.5",
        "# reference: Barnett et al. (2000)",
        f"# project_id: {project.id}",
        f"# title: {project.title}",
    ]
    for token in sorted(project.tokens, key=lambda item: (item.utterance_id or "", item.position)):
        fields = [
            "TOK",
            token.utterance_id or "",
            str(token.position),
            token.id,
            token.surface.replace("\t", " "),
            token.language or "und",
            token.speaker_id or "",
        ]
        lines.append("\t".join(fields))
        sidecar = {
            "nc_class": token.nc_class,
            "nc_prefix": token.nc_prefix,
            "four_m_type": token.four_m_type,
            "sister_lang_confidence": token.sister_lang_confidence,
            "sister_lang_evidence": token.sister_lang_evidence,
            "trigger_role": token.trigger_role,
            "mixed_code_variety": token.mixed_code_variety,
            "phon_integration_score": token.phon_integration_score,
        }
        lines.append("XIMB\t" + token.id + "\t" + json.dumps(sidecar, ensure_ascii=True, sort_keys=True))
    return "\n".join(lines) + "\n"


def validate_lides(text: str) -> ValidationReport:
    """Run an offline structural validation of a LIDES-oriented export."""

    errors: list[str] = []
    warnings: list[str] = []
    losses = [
        "LIDES comparison view may not round-trip all Imbizo memo text.",
        "LIDES comparison view represents v1.5 fields as Imbizo sidecar JSON.",
    ]
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "# IMBIZO_LIDES 1.5":
        errors.append("Missing IMBIZO_LIDES 1.5 header.")
    token_ids: set[str] = set()
    sidecar_ids: set[str] = set()
    for line in lines:
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[0] == "TOK":
            if len(parts) != 7:
                errors.append(f"Malformed TOK line: {line}")
                continue
            token_ids.add(parts[3])
        elif parts[0] == "XIMB":
            if len(parts) != 3:
                errors.append(f"Malformed XIMB line: {line}")
                continue
            sidecar_ids.add(parts[1])
            try:
                json.loads(parts[2])
            except json.JSONDecodeError as exc:
                errors.append(f"Malformed sidecar JSON for {parts[1]}: {exc}")
        else:
            errors.append(f"Unknown LIDES line type: {parts[0]}")
    missing_sidecars = sorted(token_ids - sidecar_ids)
    if missing_sidecars:
        warnings.append(f"Missing Imbizo sidecars for {len(missing_sidecars)} token(s).")
    return ValidationReport(valid=not errors, errors=errors, warnings=warnings, documented_losses=losses)


def export_lides_json(
    tokens: list[Token],
    out_path: Path,
    project_metadata: dict[str, Any] | None = None,
    sidecar: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible file helper for older tests and scripts."""

    project = Project(
        id=str((project_metadata or {}).get("id", "project")),
        title=str((project_metadata or {}).get("title", "Imbizo-CS project")),
        tokens=tokens,
        metadata={**(project_metadata or {}), "sidecar": sidecar or {}},
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(to_lides(project), encoding="utf-8")
