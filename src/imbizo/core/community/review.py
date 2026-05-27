"""Offline community-review packet workflow.

Review packets are zip files designed for USB-based peer review where
persistent internet is unavailable. Import queues reviews as pending by
default; automatic application requires an explicit `auto_apply=True` call and
is logged as provenance (Carroll et al., 2020).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tomllib
import uuid
import zipfile

from ..annotation import Project


VALID_TARGET_KINDS = {
    "token",
    "utterance",
    "concord_link",
    "four_m_audit",
    "trigger_link",
    "mixed_code_span",
    "phonological_feature",
    "dictionary_entry",
}
VALID_STATUSES = {"pending", "accepted", "rejected", "superseded"}


@dataclass(slots=True)
class CommunityReview:
    """Offline community-review record."""

    id: str
    target_kind: str
    target_id: str
    reviewer_alias: str
    comment: str
    status: str = "pending"
    signature_hash: str | None = None
    created_at: str | None = None
    applied_at: str | None = None


@dataclass(slots=True)
class ReviewPacketReport:
    """Validation summary for an offline review packet."""

    packet_path: Path
    packet_id: str
    reviewer_alias: str
    valid: bool
    errors: list[str]
    signature_hash: str | None


@dataclass(slots=True)
class ReviewImportReport:
    """Result of importing a review packet into a project."""

    packet_path: Path
    packet_id: str
    imported_count: int
    applied_count: int
    pending_count: int
    provenance_event_written: bool
    errors: list[str]


def export_review_packet(
    project: Project,
    target_kinds: list[str],
    reviewer_alias: str,
    out_path: Path,
) -> Path:
    """Export an offline-shareable community review packet.

    The zip contains a manifest, human-readable diff, review JSON, and a
    signature hash. It is designed for USB-based peer review when persistent
    internet is unavailable.
    """

    invalid = sorted(set(target_kinds) - VALID_TARGET_KINDS)
    if invalid:
        raise ValueError(f"Unsupported target kind(s): {', '.join(invalid)}")
    packet_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    reviews = [
        CommunityReview(
            id=str(uuid.uuid4()),
            target_kind=kind,
            target_id=f"{project.id}:{kind}",
            reviewer_alias=reviewer_alias,
            comment=f"Pending offline review for {kind}.",
            status="pending",
            created_at=created_at,
        )
        for kind in target_kinds
    ]
    review_json = json.dumps([asdict(review) for review in reviews], ensure_ascii=True, indent=2, sort_keys=True)
    diff_text = _human_diff(project, target_kinds)
    signature_text = f"{packet_id}:{reviewer_alias}:{sha256(review_json.encode('utf-8')).hexdigest()}"
    signature_hash = sha256(signature_text.encode("utf-8")).hexdigest()
    manifest = _manifest_text(packet_id, project, reviewer_alias, target_kinds, created_at, signature_hash)
    hashes = _hashes_text(
        {
            "manifest.toml": manifest,
            "DIFF.md": diff_text,
            "reviews/reviews.json": review_json,
            "SIGNATURE.txt": signature_text,
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.toml", manifest)
        archive.writestr("DIFF.md", diff_text)
        archive.writestr("reviews/reviews.json", review_json)
        archive.writestr("SIGNATURE.txt", signature_text)
        archive.writestr("hashes/SHA256SUMS.txt", hashes)
    return out_path


def import_review_packet(
    project: Project,
    packet_path: Path,
    auto_apply: bool = False,
) -> ReviewImportReport:
    """Import a peer-review packet into a project.

    By default, reviews are queued as pending. `auto_apply=True` requires
    explicit user confirmation by the caller and writes a provenance event.
    """

    report = validate_review_packet(packet_path)
    if not report.valid:
        return ReviewImportReport(packet_path, report.packet_id, 0, 0, 0, False, report.errors)

    with zipfile.ZipFile(packet_path) as archive:
        review_data = json.loads(archive.read("reviews/reviews.json").decode("utf-8"))
    reviews = [CommunityReview(**item) for item in review_data]
    imported = len(reviews)
    applied = 0
    pending = imported
    if auto_apply:
        applied = imported
        pending = 0
        for review in reviews:
            review.status = "accepted"
            review.applied_at = datetime.now(UTC).isoformat()
    if project.project_path:
        _write_project_review_queue(Path(project.project_path), reviews)
        if auto_apply:
            _write_provenance(Path(project.project_path), project.id, report.packet_id, imported)
    return ReviewImportReport(
        packet_path=packet_path,
        packet_id=report.packet_id,
        imported_count=imported,
        applied_count=applied,
        pending_count=pending,
        provenance_event_written=bool(auto_apply and project.project_path),
        errors=[],
    )


def create_review_packet(
    packet_path: Path,
    reviewer_alias: str,
    review_scope: str,
    changed_files: list[Path],
    diff_text: str,
    signature_text: str | None = None,
) -> Path:
    """Backward-compatible low-level review-packet helper."""

    project = Project(id="local", title=review_scope, tokens=[])
    return export_review_packet(project, ["dictionary_entry"], reviewer_alias, packet_path)


def validate_review_packet(packet_path: Path) -> ReviewPacketReport:
    """Validate hashes and required files in a local review packet."""

    errors: list[str] = []
    manifest_data: dict[str, object] = {}
    signature_hash: str | None = None
    with zipfile.ZipFile(packet_path) as archive:
        names = set(archive.namelist())
        required = {"manifest.toml", "SIGNATURE.txt", "DIFF.md", "reviews/reviews.json", "hashes/SHA256SUMS.txt"}
        errors.extend(f"missing {name}" for name in sorted(required - names))
        if "manifest.toml" in names:
            manifest_data = tomllib.loads(archive.read("manifest.toml").decode("utf-8"))
        expected_hashes = (
            _parse_hashes(archive.read("hashes/SHA256SUMS.txt").decode("utf-8"))
            if "hashes/SHA256SUMS.txt" in names
            else {}
        )
        for name, expected in expected_hashes.items():
            if name not in names:
                errors.append(f"hashed file missing: {name}")
                continue
            actual = sha256(archive.read(name)).hexdigest()
            if actual != expected:
                errors.append(f"hash mismatch: {name}")
        if "SIGNATURE.txt" in names:
            signature_hash = sha256(archive.read("SIGNATURE.txt")).hexdigest()
            expected_signature = manifest_data.get("signature_hash")
            if expected_signature and signature_hash != expected_signature:
                errors.append("signature hash does not match manifest")
    return ReviewPacketReport(
        packet_path=packet_path,
        packet_id=str(manifest_data.get("packet_id", "")),
        reviewer_alias=str(manifest_data.get("reviewer_alias", "")),
        valid=not errors,
        errors=errors,
        signature_hash=signature_hash,
    )


def persist_community_review(conn: sqlite3.Connection, review: CommunityReview) -> None:
    """Persist one community-review record to SQLite."""

    if review.target_kind not in VALID_TARGET_KINDS:
        raise ValueError(f"invalid target_kind: {review.target_kind}")
    if review.status not in VALID_STATUSES:
        raise ValueError(f"invalid review status: {review.status}")
    created_at = review.created_at or datetime.now(UTC).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO community_reviews (
            id, target_kind, target_id, reviewer_alias, comment, status,
            signature_hash, created_at, applied_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review.id,
            review.target_kind,
            review.target_id,
            review.reviewer_alias,
            review.comment,
            review.status,
            review.signature_hash,
            created_at,
            review.applied_at,
        ),
    )


def load_reviews_from_json(path: Path) -> list[CommunityReview]:
    """Load review records from a local JSON file."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return [CommunityReview(**item) for item in data]


def _manifest_text(
    packet_id: str,
    project: Project,
    reviewer_alias: str,
    target_kinds: list[str],
    created_at: str,
    signature_hash: str,
) -> str:
    targets = "\n".join(f'  "{kind}",' for kind in target_kinds)
    return (
        f'packet_id = "{packet_id}"\n'
        f'project_id = "{project.id}"\n'
        f'project_title = "{project.title}"\n'
        f'reviewer_alias = "{reviewer_alias}"\n'
        f'created_at = "{created_at}"\n'
        f'signature_hash = "{signature_hash}"\n'
        "target_kinds = [\n"
        f"{targets}\n"
        "]\n"
    )


def _human_diff(project: Project, target_kinds: list[str]) -> str:
    return (
        "# Imbizo-CS Offline Review Packet\n\n"
        f"Project: {project.title} (`{project.id}`)\n\n"
        "Targets queued for review:\n"
        + "\n".join(f"- {kind}" for kind in target_kinds)
        + "\n\nNo changes are auto-applied on import unless the researcher explicitly enables auto_apply.\n"
    )


def _hashes_text(files: dict[str, str]) -> str:
    return "\n".join(f"{sha256(text.encode('utf-8')).hexdigest()}  {name}" for name, text in files.items()) + "\n"


def _parse_hashes(text: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        hashes[name.strip()] = digest
    return hashes


def _write_project_review_queue(project_path: Path, reviews: list[CommunityReview]) -> None:
    review_dir = project_path / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    out_path = review_dir / "pending_reviews.json"
    existing: list[dict[str, object]] = []
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
    existing.extend(asdict(review) for review in reviews)
    out_path.write_text(json.dumps(existing, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")


def _write_provenance(project_path: Path, project_id: str, packet_id: str, imported_count: int) -> None:
    log_dir = project_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": "community_review.auto_apply",
        "project_id": project_id,
        "packet_id": packet_id,
        "imported_count": imported_count,
    }
    with (log_dir / "provenance.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
