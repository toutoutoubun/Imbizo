"""Offline loader for bootstrap-installed morphologically annotated corpora."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class MorphAnnotatedCorpus:
    """A local morphologically annotated corpus for one language."""

    iso: str
    corpus_file: Path
    tag_inventory: dict[str, int]

    def tag_frequency(self, prefix: str) -> dict[str, int]:
        """Return tag frequencies whose tag begins with `prefix`."""

        folded = prefix.casefold()
        return {tag: count for tag, count in self.tag_inventory.items() if tag.casefold().startswith(folded)}


def load_morph_corpus(iso: str, root: Path = Path("corpora/morph_annotated")) -> MorphAnnotatedCorpus:
    """Load a bootstrap-installed morphologically annotated corpus index."""

    index_path = root / iso / "index.yaml"
    if not index_path.exists():
        return MorphAnnotatedCorpus(iso=iso, corpus_file=root / iso / f"{iso}_morph.txt", tag_inventory={})
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    corpus_file = root / iso / str(payload.get("corpus_file", f"{iso}_morph.txt"))
    inventory = payload.get("tag_inventory")
    if isinstance(inventory, dict):
        return MorphAnnotatedCorpus(iso=iso, corpus_file=corpus_file, tag_inventory={str(k): int(v) for k, v in inventory.items()})
    return MorphAnnotatedCorpus(iso=iso, corpus_file=corpus_file, tag_inventory=_scan_tags(corpus_file))


def _scan_tags(corpus_file: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    if not corpus_file.exists():
        return {}
    for line in corpus_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        for tag in parts[1].replace("|", "+").split("+"):
            if tag:
                counts[tag] += 1
    return dict(sorted(counts.items()))
