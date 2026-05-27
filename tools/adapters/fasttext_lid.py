"""Adapter for fastText lid.176 language identification models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import write_index, write_processing_provenance
from tools.adapters.utils.provenance import sha256_of

SUPPORTED_CODES = ["af", "zu", "xh", "st", "tn", "en", "eng", "afr", "zul", "xho", "sot", "tsn"]

CAVEATS = (
    "This model is an offline baseline language identifier from fastText "
    "lid.176 (Joulin et al. 2017). Entries are unverified; treat them as "
    "starting suggestions, not authoritative claims. It is useful for Layer 1 "
    "screening, not final code-switching interpretation."
)


class FastTextLidAdapter(SourceAdapter):
    """Install a downloaded fastText lid.176 model and write an index."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Copy the verified model and write models/lid/index.yaml."""

        if not output_dirs:
            raise ValueError("fastText LID conversion requires models/lid output directory.")
        out_dir = output_dirs[0]
        out_dir.mkdir(parents=True, exist_ok=True)
        if raw_path.suffix not in {".ftz", ".bin"}:
            raise ValueError(f"Unexpected fastText model suffix: {raw_path.suffix}")
        model_path = out_dir / raw_path.name
        model_path.write_bytes(raw_path.read_bytes())
        index_path = write_index(
            out_dir / "index.yaml",
            resource_kind="model",
            languages=SUPPORTED_CODES,
            usable_by=["F4_lid_baseline", "core.lid.baseline"],
            source_metadata=source_metadata,
            raw_path=raw_path,
            adapter_path="tools/adapters/fasttext_lid.py",
            adapter_version=self.adapter_version,
            caveats=CAVEATS,
            extra={
                "model_file": model_path.name,
                "model_sha256": sha256_of(model_path),
                "fasttext_python_usage": "fasttext.load_model('models/lid/lid.176.ftz').predict(text, k=3)",
            },
        )
        provenance = write_processing_provenance(str(source_metadata.get("id", "fasttext_lid176")), raw_path, [model_path, index_path], source_metadata)
        return [model_path, index_path, provenance]


Adapter = FastTextLidAdapter
