"""Adapter for optional whisper.cpp local ASR resources."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import unpack_archive, write_index, write_processing_provenance

DISCLAIMER = """# Whisper.cpp ASR Quality Disclaimer

Whisper.cpp is optional. It is not part of the Imbizo-CS MVP default workflow.
Accuracy on isiZulu, isiXhosa, Sesotho, Setswana, and other South African Bantu
languages is uncertain and may be poor. Use output only as a starting transcript
for human correction, never as authoritative evidence.
"""

CAVEATS = (
    "This optional ASR resource was installed only after explicit acceptance. "
    "Entries are unverified; treat them as starting suggestions, not authoritative "
    "claims. Manual transcription remains the default Imbizo-CS workflow."
)


class WhisperCppAdapter(SourceAdapter):
    """Install optional whisper.cpp source/model artifacts after explicit consent."""

    def convert(self, raw_path: Path, output_dirs: list[Path], source_metadata: Mapping[str, Any]) -> list[Path]:
        """Refuse unless include_asr and IMBIZO_ASR_ACCEPTED=1 are both present."""

        if not source_metadata.get("include_asr"):
            raise ValueError("whisper.cpp is opt-in; rerun bootstrap with --include-asr.")
        if os.environ.get("IMBIZO_ASR_ACCEPTED") != "1":
            raise ValueError("Set IMBIZO_ASR_ACCEPTED=1 to acknowledge the ASR quality disclaimer.")
        if not output_dirs:
            raise ValueError("Whisper.cpp conversion requires processing/whisper_cpp output directory.")
        source_dir = output_dirs[0]
        source_files = unpack_archive(raw_path, source_dir / "source")
        disclaimer = source_dir / "QUALITY_DISCLAIMER.md"
        disclaimer.parent.mkdir(parents=True, exist_ok=True)
        disclaimer.write_text(DISCLAIMER, encoding="utf-8")
        index = write_index(
            source_dir / "index.yaml",
            resource_kind="toolkit",
            languages=[],
            usable_by=["optional_local_asr_plugin"],
            source_metadata=source_metadata,
            raw_path=raw_path,
            adapter_path="tools/adapters/whisper_cpp.py",
            adapter_version=self.adapter_version,
            caveats=CAVEATS,
            extra={
                "quality_disclaimer": disclaimer.name,
                "opt_in_required": True,
                "source_file_count": len(source_files),
            },
        )
        provenance = write_processing_provenance(str(source_metadata.get("id", "whisper_cpp_optional")), raw_path, [disclaimer, index], source_metadata)
        return [disclaimer, index, provenance]


Adapter = WhisperCppAdapter
