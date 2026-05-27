"""Pydantic v2 models mirroring the project export schema."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProjectExportLanguage(BaseModel):
    """Language label in a project export."""

    id: str = Field(description="Stable language row identifier.")
    code: str = Field(description="ISO 639-3 code or project-defined code.")
    name: str = Field(description="Display name.")
    autonym: str = Field(default="", description="Language self-name where known.")
    category: str = Field(default="language", description="Language, special label, or user-defined variety.")
    color_hex: str = Field(default="#808080", description="Language legend color.")


class ProjectExportAnnotation(BaseModel):
    """Code-switching annotation object in project JSON export."""

    id: str = Field(description="Stable annotation identifier.")
    token_id: str | None = Field(default=None, description="Target token identifier.")
    segment_id: str | None = Field(default=None, description="Target segment identifier.")
    source: Literal["manual", "auto", "imported"] = Field(description="Annotation origin.")
    status: Literal["active", "rejected", "superseded"] = Field(default="active", description="Annotation lifecycle state.")
    language_id: str | None = Field(default=None, description="Language label.")
    matrix_language_id: str | None = Field(default=None, description="Matrix Language label.")
    embedded_language_id: str | None = Field(default=None, description="Embedded Language label.")
    switch_type: str | None = Field(default=None, description="Intra-, inter-, or extra-sentential switch type.")
    linguistic_status: str | None = Field(default=None, description="Borrowing, insertion, or alternation.")
    trigger_text: str = Field(default="", description="Trigger word or phrase.")
    researcher_confidence: int | None = Field(default=None, description="Researcher confidence from 1 to 5.")
    memo: str = Field(default="", description="Free-text qualitative memo.")


class ProjectExportProvenance(BaseModel):
    """Append-only provenance entry in project JSON export."""

    id: str = Field(description="Stable provenance identifier.")
    event_type: str = Field(description="Import, auto_label, manual_update, metric_run, export, or error.")
    actor_type: str = Field(description="Researcher, system, importer, LID layer, metric, or exporter.")
    target_table: str = Field(default="", description="Target SQLite table.")
    target_id: str = Field(default="", description="Target record identifier.")
    tool_name: str = Field(default="", description="Tool or provider name.")
    tool_version: str = Field(default="", description="Tool or provider version.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured event payload.")
    created_at: str = Field(description="UTC timestamp.")


class ProjectExportMetricResult(BaseModel):
    """Metric snapshot in project JSON export."""

    id: str = Field(description="Stable metric result identifier.")
    metric_run_id: str = Field(description="Metric run identifier.")
    metric_name: str = Field(description="Metric name.")
    scope_type: str = Field(description="Project, speaker, scene, segment, or custom filter.")
    scope_id: str = Field(default="", description="Optional scope identifier.")
    value: Any = Field(description="Metric value.")
    input_count: int = Field(description="Number of input records used.")


class ProjectExport(BaseModel):
    """Full Imbizo-CS project JSON export."""

    schema_version: int = Field(description="Project export schema version.")
    exported_at: str = Field(description="UTC export timestamp.")
    project: dict[str, Any] = Field(description="Project metadata.")
    languages: list[ProjectExportLanguage] = Field(description="Project language labels.")
    annotations: list[ProjectExportAnnotation] = Field(default_factory=list, description="Annotation records.")
    provenance: list[ProjectExportProvenance] = Field(default_factory=list, description="Provenance records.")
    metrics: list[ProjectExportMetricResult] = Field(default_factory=list, description="Metric result snapshots.")
