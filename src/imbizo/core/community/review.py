"""Offline community review packet workflow.

Community review supports local dictionary correction without requiring
persistent internet access. The workflow follows data-sovereignty and CARE
principles by keeping review packets inspectable, portable, and project-local
(Carroll et al., 2020).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tomllib
import uuid
import zipfile


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


def create_review_packet(
    packet_path: Path,
    reviewer_alias: str,
    review_scope: str,
    changed_files: list[Path],
    diff_text: str,
    signature_text: str | None = None,
) -> Path:
    """Create a local zip review packet with manifest, signature, diff, and hashes."""

    packet_id = str(uuid.uuid4())
    signature = signature_text or f"Local attestation by {reviewer_alias} at {datetime.now(UTC).isoformat()}"
    manifest = _manifest_text(packet_id, reviewer_alias, review_scope, changed_files)
    hashes = _hashes_text(changed_files, extra={"SIGNATURE.txt": signature, "DIFF.md": diff_text})
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.toml", manifest)
        archive.writestr("SIGNATURE.txt", signature)
        archive.writestr("DIFF.md", diff_text)
        archive.writestr("hashes/SHA256SUMS.txt", hashes)
        for file_path in changed_files:
            archive.write(file_path, f"changes/{file_path.name}")
    return packet_path


def validate_review_packet(packet_path: Path) -> ReviewPacketReport:
    """Validate hashes and required files in a local review packet."""

    errors: list[str] = []
    with zipfile.ZipFile(packet_path) as archive:
        names = set(archive.namelist())
        required = {"manifest.toml", "SIGNATURE.txt", "DIFF.md", "hashes/SHA256SUMS.txt"}
        missing = sorted(required - names)
        errors.extend(f"missing {name}" for name in missing)
        manifest_data: dict[str, object] = {}
        if "manifest.toml" in names:
            manifest_data = tomllib.loads(archive.read("manifest.toml").decode("utf-8"))
        expected_hashes = _parse_hashes(
            archive.read("hashes/SHA256SUMS.txt").decode("utf-8")
        ) if "hashes/SHA256SUMS.txt" in names else {}
        for name, expected in expected_hashes.items():
            if name not in names:
                errors.append(f"hashed file missing: {name}")
                continue
            actual = sha256(archive.read(name)).hexdigest()
            if actual != expected:
                errors.append(f"hash mismatch: {name}")
        signature_hash = sha256(archive.read("SIGNATURE.txt")).hexdigest() if "SIGNATURE.txt" in names else None
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
    """Load review records from a local JSON file in a review packet."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return [CommunityReview(**item) for item in data]


def _manifest_text(packet_id: str, reviewer_alias: str, review_scope: str, changed_files: list[Path]) -> str:
    files = "\n".join(f'  "{path.name}",' for path in changed_files)
    return (
        f'packet_id = "{packet_id}"\n'
        f'reviewer_alias = "{reviewer_alias}"\n'
        f'review_scope = "{review_scope}"\n'
        f'created_at = "{datetime.now(UTC).isoformat()}"\n'
        "changed_files = [\n"
        f"{files}\n"
        "]\n"
    )


def _hashes_text(changed_files: list[Path], extra: dict[str, str]) -> str:
    lines = []
    for name, text in extra.items():
        lines.append(f"{sha256(text.encode('utf-8')).hexdigest()}  {name}")
    for file_path in changed_files:
        lines.append(f"{sha256(file_path.read_bytes()).hexdigest()}  changes/{file_path.name}")
    return "\n".join(lines) + "\n"


def _parse_hashes(text: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        hashes[name.strip()] = digest
    return hashes
