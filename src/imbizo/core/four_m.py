"""4-M model hint loading, suggestion, audit, and SQLite persistence.

The 4-M layer supports Matrix Language Frame analysis by distinguishing content
morphemes, early system morphemes, bridge late system morphemes, and outsider
late system morphemes (Myers-Scotton, 2002; Jake, Myers-Scotton & Gross, 2002).
It is optional and advisory: the software records evidence and reviewer
decisions, but it does not force MLF analysis over alternatives such as
Muysken's typology (Muysken, 2000).
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from imbizo.app.time import utc_now
from imbizo.core.concord import ConcordLink
from imbizo.domain.transcripts import Token


FourMType = Literal["content", "early_system", "bridge_late_system", "outsider_late_system"]
ReviewSource = Literal["manual", "suggested-accepted", "suggested-overridden"]
AuditVerdict = Literal["compatible", "possibly_compatible", "inconclusive", "tension", "not_applicable"]

VALID_FOUR_M_TYPES = {"content", "early_system", "bridge_late_system", "outsider_late_system"}
VALID_REVIEW_SOURCES = {"manual", "suggested-accepted", "suggested-overridden"}
VALID_AUDIT_VERDICTS = {"compatible", "possibly_compatible", "inconclusive", "tension", "not_applicable"}


@dataclass(slots=True)
class FourMHint:
    """One dictionary hint for a 4-M morpheme type."""

    form: str
    english_gloss: str
    four_m_type: FourMType
    type_justification: str
    verified: bool
    note: str = ""


@dataclass(slots=True)
class FourMDictionary:
    """Parsed 4-M hint dictionary with provenance metadata."""

    language_code: str
    language_name: str
    version: str
    source: str
    last_reviewed_by: str
    last_reviewed_on: str
    hints: list[FourMHint] = field(default_factory=list)
    path: Path | None = None


@dataclass(slots=True)
class FourMSuggestion:
    """Ranked 4-M suggestion for a token surface."""

    language_code: str
    form: str
    english_gloss: str
    four_m_type: FourMType
    type_justification: str
    verified: bool
    note: str
    rank: int
    source: str


@dataclass(slots=True)
class TokenForFourM:
    """Minimal token view used by the 4-M audit helper."""

    id: str
    segment_id: str
    token_text: str
    sort_order: int
    language_id: str | None = None
    four_m_type: FourMType | None = None


@dataclass(slots=True)
class FourMAudit:
    """Persistable audit record for one segment."""

    id: str
    segment_id: str
    verdict: AuditVerdict
    source: ReviewSource
    checker_version: str
    explanation: str
    matrix_language_id: str | None = None
    embedded_language_id: str | None = None
    system_morpheme_count: int = 0
    outsider_late_system_morpheme_count: int = 0
    content_morpheme_switch_count: int = 0
    confirmed_concord_link_count: int = 0
    reviewed_concord_link_count: int = 0
    integration_score: float | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class MLFVerdict:
    """Advisory 4-M compatibility verdict for one utterance."""

    status: Literal["consistent", "mixed", "insufficient_data"]
    evidence: list[dict[str, str]]
    recommended_review: bool
    narrative: str


def load_four_m_dictionary(path: Path) -> FourMDictionary:
    """Load a local 4-M YAML hint dictionary."""

    data = _load_yaml_mapping(path)
    hints: list[FourMHint] = []
    raw_hints = data.get("four_m_hints", {})
    if not isinstance(raw_hints, dict):
        raise ValueError(f"`four_m_hints` must be a mapping in {path}")
    for four_m_type, entries in raw_hints.items():
        if four_m_type not in VALID_FOUR_M_TYPES:
            raise ValueError(f"Unsupported 4-M type `{four_m_type}` in {path}")
        for raw_entry in _as_list(entries, str(four_m_type)):
            hints.append(
                FourMHint(
                    form=str(raw_entry.get("form", "")),
                    english_gloss=str(raw_entry.get("english_gloss", "")),
                    four_m_type=four_m_type,  # type: ignore[arg-type]
                    type_justification=str(raw_entry.get("type_justification", "")),
                    verified=bool(raw_entry.get("verified", False)),
                    note=str(raw_entry.get("note", "")),
                )
            )
    return FourMDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        last_reviewed_by=str(data["last_reviewed_by"]),
        last_reviewed_on=str(data["last_reviewed_on"]),
        hints=hints,
        path=path,
    )


def load_default_four_m_dictionary(language_code: str, project_path: Path | None = None) -> FourMDictionary:
    """Load a project override or shipped 4-M hint dictionary for a language."""

    for root in _dictionary_roots(project_path):
        candidate = root / "four_m" / f"{language_code}.yaml"
        if candidate.exists():
            return load_four_m_dictionary(candidate)
    raise FileNotFoundError(f"No 4-M dictionary found for language code: {language_code}")


def check_mlf_compatibility(utterance_tokens: list[Token]) -> MLFVerdict:
    """Assess whether 4-M tags suggest one Matrix Language.

    The checker examines assigned 4-M tags and token language IDs in one
    utterance and reports whether system morphemes appear consistent with a
    single Matrix Language under the System Morpheme Principle. The verdict is
    advisory and never overrides researcher annotations (Myers-Scotton, 1993;
    Myers-Scotton, 2002; Jake, Myers-Scotton & Gross, 2002).
    """

    evidence: list[dict[str, str]] = []
    system_languages: set[str] = set()
    missing_language = False
    for token in utterance_tokens:
        four_m_type = getattr(token, "four_m_type", None)
        language_id = getattr(token, "language_id", None)
        if four_m_type is None:
            continue
        evidence.append({"token_id": token.id, "four_m_type": str(four_m_type), "language_id": str(language_id or "")})
        if four_m_type in {"early_system", "bridge_late_system", "outsider_late_system"}:
            if language_id:
                system_languages.add(str(language_id))
            else:
                missing_language = True
    if not evidence or missing_language or not system_languages:
        return MLFVerdict(
            status="insufficient_data",
            evidence=evidence,
            recommended_review=True,
            narrative="There are not enough reviewed 4-M and language labels to assess Matrix Language compatibility.",
        )
    if len(system_languages) == 1:
        language = sorted(system_languages)[0]
        return MLFVerdict(
            status="consistent",
            evidence=evidence,
            recommended_review=False,
            narrative=f"Reviewed system morphemes point to one language ({language}); this is advisory evidence only.",
        )
    return MLFVerdict(
        status="mixed",
        evidence=evidence,
        recommended_review=True,
        narrative=(
            "Reviewed system morphemes point to more than one language. "
            "This may indicate mixed structure, uncertain tags, or a case better handled outside a strict MLF account."
        ),
    )


def suggest_four_m_type(token_surface: str, language_code: str) -> list[FourMSuggestion]:
    """Return exact-form 4-M hints for a token surface.

    Exact matching keeps the helper transparent and low-resource. It is
    deliberately conservative because 4-M classification is theoretical
    analysis, not a mechanical property of a string (Myers-Scotton, 2002).
    """

    dictionary = load_default_four_m_dictionary(language_code)
    surface = token_surface.strip().lower()
    suggestions: list[FourMSuggestion] = []
    for hint in dictionary.hints:
        if hint.form.strip().lower() != surface:
            continue
        suggestions.append(
            FourMSuggestion(
                language_code=dictionary.language_code,
                form=hint.form,
                english_gloss=hint.english_gloss,
                four_m_type=hint.four_m_type,
                type_justification=hint.type_justification,
                verified=hint.verified,
                note=hint.note,
                rank=0,
                source=dictionary.source,
            )
        )
    suggestions.sort(key=lambda item: (not item.verified, item.four_m_type, item.form))
    for index, suggestion in enumerate(suggestions, start=1):
        suggestion.rank = index
    return suggestions


def save_token_four_m_type(
    connection: sqlite3.Connection,
    token_id: str,
    four_m_type: FourMType | None,
    four_m_source: ReviewSource,
) -> None:
    """Persist a reviewed 4-M type on a token."""

    if four_m_type is not None and four_m_type not in VALID_FOUR_M_TYPES:
        raise ValueError("four_m_type is outside the v1.0 controlled vocabulary.")
    _validate_review_source(four_m_source)
    _require_token_columns(connection)
    cursor = connection.execute(
        """
        UPDATE tokens
        SET four_m_type = ?, four_m_source = ?
        WHERE id = ?
        """,
        (four_m_type, four_m_source, token_id),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Token not found: {token_id}")
    connection.commit()


def audit_segment(
    segment_id: str,
    tokens: list[TokenForFourM],
    concord_links: list[ConcordLink],
    *,
    matrix_language_id: str | None = None,
    embedded_language_id: str | None = None,
    source: ReviewSource = "manual",
    checker_version: str = "1.0.0",
) -> FourMAudit:
    """Create a transparent 4-M audit summary for one utterance.

    The audit checks counts that may be useful for the System Morpheme
    Principle, but it intentionally returns descriptive verdicts rather than
    forcing a theory (Myers-Scotton, 1993; Myers-Scotton, 2002).
    """

    _validate_review_source(source)
    segment_tokens = [token for token in tokens if token.segment_id == segment_id]
    segment_links = [link for link in concord_links if link.segment_id == segment_id]
    reviewed = [link for link in segment_links if link.agreement_status in {"confirmed", "mismatch", "uncertain"}]
    confirmed = [link for link in reviewed if link.agreement_status == "confirmed"]
    system_count = sum(1 for token in segment_tokens if token.four_m_type in {"early_system", "bridge_late_system", "outsider_late_system"})
    outsider_count = sum(1 for token in segment_tokens if token.four_m_type == "outsider_late_system")
    content_switch_count = _content_switch_count(segment_tokens)
    integration_score = len(confirmed) / len(reviewed) if reviewed else None
    verdict = _verdict(segment_tokens, reviewed, confirmed)
    explanation = _explain(verdict, len(confirmed), len(reviewed), outsider_count, content_switch_count)
    now = utc_now()
    return FourMAudit(
        id=str(uuid.uuid4()),
        segment_id=segment_id,
        verdict=verdict,
        matrix_language_id=matrix_language_id,
        embedded_language_id=embedded_language_id,
        system_morpheme_count=system_count,
        outsider_late_system_morpheme_count=outsider_count,
        content_morpheme_switch_count=content_switch_count,
        confirmed_concord_link_count=len(confirmed),
        reviewed_concord_link_count=len(reviewed),
        integration_score=integration_score,
        source=source,
        checker_version=checker_version,
        explanation=explanation,
        created_at=now,
        updated_at=now,
    )


def save_four_m_audit(connection: sqlite3.Connection, audit: FourMAudit) -> None:
    """Persist a 4-M audit record."""

    _validate_audit(audit)
    _require_table(connection, "four_m_audit")
    now = utc_now()
    created_at = audit.created_at or now
    updated_at = audit.updated_at or now
    connection.execute(
        """
        INSERT INTO four_m_audit (
            id, segment_id, verdict, matrix_language_id, embedded_language_id,
            system_morpheme_count, outsider_late_system_morpheme_count,
            content_morpheme_switch_count, confirmed_concord_link_count,
            reviewed_concord_link_count, integration_score, source,
            checker_version, explanation, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            verdict = excluded.verdict,
            matrix_language_id = excluded.matrix_language_id,
            embedded_language_id = excluded.embedded_language_id,
            system_morpheme_count = excluded.system_morpheme_count,
            outsider_late_system_morpheme_count = excluded.outsider_late_system_morpheme_count,
            content_morpheme_switch_count = excluded.content_morpheme_switch_count,
            confirmed_concord_link_count = excluded.confirmed_concord_link_count,
            reviewed_concord_link_count = excluded.reviewed_concord_link_count,
            integration_score = excluded.integration_score,
            source = excluded.source,
            checker_version = excluded.checker_version,
            explanation = excluded.explanation,
            updated_at = excluded.updated_at
        """,
        (
            audit.id,
            audit.segment_id,
            audit.verdict,
            audit.matrix_language_id,
            audit.embedded_language_id,
            audit.system_morpheme_count,
            audit.outsider_late_system_morpheme_count,
            audit.content_morpheme_switch_count,
            audit.confirmed_concord_link_count,
            audit.reviewed_concord_link_count,
            audit.integration_score,
            audit.source,
            audit.checker_version,
            audit.explanation,
            created_at,
            updated_at,
        ),
    )
    connection.commit()


def list_four_m_audits(connection: sqlite3.Connection, segment_id: str | None = None) -> list[FourMAudit]:
    """Return stored 4-M audits, optionally filtered by segment."""

    _require_table(connection, "four_m_audit")
    if segment_id is None:
        rows = connection.execute("SELECT * FROM four_m_audit ORDER BY segment_id, created_at").fetchall()
    else:
        rows = connection.execute("SELECT * FROM four_m_audit WHERE segment_id = ? ORDER BY created_at", (segment_id,)).fetchall()
    return [_audit_from_row(row) for row in rows]


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    for key in ("language_code", "language_name", "version", "source", "last_reviewed_by", "last_reviewed_on"):
        if key not in data:
            raise ValueError(f"Missing required key `{key}` in {path}")
    return data


def _as_list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"`{name}` must be a list.")
    return value


def _dictionary_roots(project_path: Path | None) -> list[Path]:
    roots: list[Path] = []
    if project_path is not None:
        roots.append(project_path.expanduser().resolve() / "dictionaries")
    roots.append(Path(__file__).resolve().parents[3] / "dictionaries")
    return roots


def _content_switch_count(tokens: list[TokenForFourM]) -> int:
    count = 0
    previous_language: str | None = None
    for token in sorted(tokens, key=lambda item: item.sort_order):
        if token.four_m_type != "content" or token.language_id is None:
            continue
        if previous_language is not None and token.language_id != previous_language:
            count += 1
        previous_language = token.language_id
    return count


def _verdict(tokens: list[TokenForFourM], reviewed: list[ConcordLink], confirmed: list[ConcordLink]) -> AuditVerdict:
    if not tokens:
        return "not_applicable"
    if not any(token.four_m_type for token in tokens):
        return "inconclusive"
    if reviewed and len(confirmed) == len(reviewed):
        return "possibly_compatible"
    if reviewed and not confirmed:
        return "tension"
    return "inconclusive"


def _explain(verdict: AuditVerdict, confirmed: int, reviewed: int, outsider_count: int, content_switch_count: int) -> str:
    return (
        f"4-M audit verdict `{verdict}` from {confirmed}/{reviewed} confirmed concord links, "
        f"{outsider_count} outsider late system morphemes, and {content_switch_count} content-morpheme switches. "
        "This is advisory evidence only; the researcher remains the final interpreter."
    )


def _validate_review_source(source: str) -> None:
    if source not in VALID_REVIEW_SOURCES:
        raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")


def _validate_audit(audit: FourMAudit) -> None:
    if audit.verdict not in VALID_AUDIT_VERDICTS:
        raise ValueError("verdict is outside the v1.0 controlled vocabulary.")
    _validate_review_source(audit.source)
    if audit.integration_score is not None and not 0.0 <= audit.integration_score <= 1.0:
        raise ValueError("integration_score must be between 0.0 and 1.0, or None.")


def _require_token_columns(connection: sqlite3.Connection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info(tokens)").fetchall()}
    missing = {"four_m_type", "four_m_source"} - existing
    if missing:
        raise RuntimeError(f"v1.0 4-M migration has not been applied; missing columns: {sorted(missing)}")


def _require_table(connection: sqlite3.Connection, table_name: str) -> None:
    row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
    if row is None:
        raise RuntimeError(f"v1.0 migration has not been applied; missing table: {table_name}")


def _audit_from_row(row: sqlite3.Row) -> FourMAudit:
    return FourMAudit(
        id=row["id"],
        segment_id=row["segment_id"],
        verdict=row["verdict"],
        matrix_language_id=row["matrix_language_id"],
        embedded_language_id=row["embedded_language_id"],
        system_morpheme_count=row["system_morpheme_count"],
        outsider_late_system_morpheme_count=row["outsider_late_system_morpheme_count"],
        content_morpheme_switch_count=row["content_morpheme_switch_count"],
        confirmed_concord_link_count=row["confirmed_concord_link_count"],
        reviewed_concord_link_count=row["reviewed_concord_link_count"],
        integration_score=row["integration_score"],
        source=row["source"],
        checker_version=row["checker_version"],
        explanation=row["explanation"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
