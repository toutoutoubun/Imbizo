"""Local speaker-scene heatmap rendering with matplotlib.

The heatmap follows a deliberately readable static-figure style: labelled axes,
in-cell values, and a legend that pairs colour with language glyphs. This is in
the spirit of reproducible quantitative display in complex-systems work such as
Goh and Barabási (2008), while relying only on matplotlib's documented static
rendering APIs. No remote fonts, CDNs, or web embeds are used.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Any, Literal

import pandas as pd

from imbizo import __version__
from imbizo.core.annotation import Project, Token

from .palette import LanguagePalette


@dataclass(slots=True)
class TokenObservation:
    """One token with the dimensions needed for visualisation."""

    token_id: str
    speaker: str
    scene: str
    language: str
    position: int
    start_time_ms: int | None = None


@dataclass(slots=True)
class HeatmapCell:
    """Aggregated language proportions for one speaker-scene cell."""

    speaker: str
    scene: str
    total_tokens: int
    proportions: dict[str, float]

    @property
    def dominant_language(self) -> str:
        """Return the highest-proportion language code, or `und`."""

        if not self.proportions:
            return "und"
        return max(self.proportions.items(), key=lambda item: (item[1], item[0]))[0]


def render_speaker_scene_heatmap(
    project: Project,
    output_path: Path,
    format: Literal["png", "svg"] = "png",
    colourblind_safe: bool = True,
    *,
    per_language: bool = False,
) -> Path | list[Path]:
    """Render a local speaker x scene language-proportion heatmap.

    The default figure colours each cell by dominant language and annotates the
    cell with glyph, language code, and proportion. With `per_language=True`, a
    separate heatmap is rendered per language with intensity representing that
    language's proportion in each speaker-scene cell.
    """

    if format not in {"png", "svg"}:
        raise ValueError("format must be 'png' or 'svg'.")
    observations = load_token_observations(project)
    cells = compute_speaker_scene_language_proportions(observations)
    languages = sorted({language for cell in cells for language in cell.proportions} or {"und"})
    palette = LanguagePalette(_project_root(project) if colourblind_safe else None)
    if per_language:
        paths: list[Path] = []
        for language in languages:
            target = output_path.with_name(f"{output_path.stem}_{language}.{format}")
            _render_language_heatmap(cells, language, target, format, project, palette)
            paths.append(target)
        return paths
    _render_dominant_heatmap(cells, output_path, format, project, palette)
    return output_path


def compute_speaker_scene_language_proportions(observations: list[TokenObservation]) -> list[HeatmapCell]:
    """Aggregate token observations into speaker-scene language proportions."""

    if not observations:
        return []
    frame = pd.DataFrame([asdict(obs) for obs in observations])
    grouped = frame.groupby(["speaker", "scene", "language"], dropna=False).size().reset_index(name="count")
    totals = grouped.groupby(["speaker", "scene"])["count"].sum().to_dict()
    cells: dict[tuple[str, str], dict[str, float]] = {}
    for row in grouped.itertuples(index=False):
        key = (str(row.speaker), str(row.scene))
        cells.setdefault(key, {})[str(row.language)] = float(row.count) / float(totals[key])
    return [
        HeatmapCell(speaker=speaker, scene=scene, total_tokens=int(totals[(speaker, scene)]), proportions=proportions)
        for (speaker, scene), proportions in sorted(cells.items())
    ]


def load_token_observations(project: Project) -> list[TokenObservation]:
    """Read token observations from SQLite when possible, otherwise from Project.tokens."""

    connection = getattr(project, "connection", None)
    if connection is not None:
        return _observations_from_connection(connection)
    database_path = _database_path(project)
    if database_path and database_path.exists():
        with sqlite3.connect(database_path) as conn:
            conn.row_factory = sqlite3.Row
            return _observations_from_connection(conn)
    return _observations_from_tokens(getattr(project, "tokens", []))


def _render_dominant_heatmap(
    cells: list[HeatmapCell], output_path: Path, format: str, project: Project, palette: LanguagePalette
) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Patch

    matplotlib.rcParams["svg.fonttype"] = "path"
    speakers, scenes = _axes(cells)
    matrix = [[(1, 1, 1) for _ in scenes] for _ in speakers]
    labels = [["" for _ in scenes] for _ in speakers]
    by_key = {(cell.speaker, cell.scene): cell for cell in cells}
    for row, speaker in enumerate(speakers):
        for col, scene in enumerate(scenes):
            cell = by_key.get((speaker, scene))
            if cell:
                lang = cell.dominant_language
                prop = cell.proportions[lang]
                matrix[row][col] = to_rgb(palette.colour_for(lang))
                labels[row][col] = f"{palette.glyph_for(lang)} {lang}\n{prop:.0%}"
    width = max(6.0, len(scenes) * 1.7)
    height = max(4.0, len(speakers) * 0.9 + 2.0)
    fig, ax = plt.subplots(figsize=(width, height), constrained_layout=True)
    ax.imshow(matrix, aspect="auto")
    ax.set_xticks(range(len(scenes)), labels=scenes, rotation=35, ha="right")
    ax.set_yticks(range(len(speakers)), labels=speakers)
    ax.set_xlabel("Scene")
    ax.set_ylabel("Speaker")
    ax.set_title("Speaker x Scene Dominant Language Heatmap")
    for row in range(len(speakers)):
        for col in range(len(scenes)):
            ax.text(col, row, labels[row][col], ha="center", va="center", fontsize=8, color="black")
    languages = sorted({cell.dominant_language for cell in cells})
    handles = [Patch(facecolor=palette.colour_for(lang), label=f"{palette.glyph_for(lang)} {lang}") for lang in languages]
    if handles:
        ax.legend(handles=handles, title="Language", loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.text(0.01, 0.01, _footer(project), fontsize=7, ha="left")
    _save_figure(fig, output_path, format, "Speaker-scene language heatmap", "Dominant language per speaker-scene cell.")


def _render_language_heatmap(
    cells: list[HeatmapCell], language: str, output_path: Path, format: str, project: Project, palette: LanguagePalette
) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    matplotlib.rcParams["svg.fonttype"] = "path"
    speakers, scenes = _axes(cells)
    by_key = {(cell.speaker, cell.scene): cell for cell in cells}
    matrix = [
        [by_key.get((speaker, scene), HeatmapCell(speaker, scene, 0, {})).proportions.get(language, 0.0) for scene in scenes]
        for speaker in speakers
    ]
    fig, ax = plt.subplots(figsize=(max(6.0, len(scenes) * 1.5), max(4.0, len(speakers) * 0.8 + 2.0)), constrained_layout=True)
    image = ax.imshow(matrix, cmap="Greys", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(scenes)), labels=scenes, rotation=35, ha="right")
    ax.set_yticks(range(len(speakers)), labels=speakers)
    ax.set_title(f"{palette.glyph_for(language)} {language} proportion by speaker and scene")
    for row in range(len(speakers)):
        for col in range(len(scenes)):
            ax.text(col, row, f"{matrix[row][col]:.0%}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label=f"{language} token proportion")
    fig.text(0.01, 0.01, _footer(project), fontsize=7, ha="left")
    _save_figure(fig, output_path, format, f"{language} proportion heatmap", f"Per-cell proportion for {language}.")


def _observations_from_connection(conn: sqlite3.Connection) -> list[TokenObservation]:
    conn.row_factory = sqlite3.Row
    tables = _tables(conn)
    token_columns = _columns(conn, "tokens")
    if "tokens" not in tables:
        return []
    if "segments" in tables and "segment_id" in token_columns:
        return _observations_from_relational_schema(conn, parent_table="segments", token_parent_column="segment_id")
    if "utterances" in tables and "utterance_id" in token_columns:
        return _observations_from_relational_schema(conn, parent_table="utterances", token_parent_column="utterance_id")
    return _observations_from_token_table(conn)


def _observations_from_relational_schema(
    conn: sqlite3.Connection,
    *,
    parent_table: Literal["segments", "utterances"],
    token_parent_column: str,
) -> list[TokenObservation]:
    tables = _tables(conn)
    token_columns = _columns(conn, "tokens")
    parent_columns = _columns(conn, parent_table)
    annotation_columns = _columns(conn, "annotations") if "annotations" in tables else set()
    language_columns = _columns(conn, "languages") if "languages" in tables else set()
    joins = [f"JOIN {parent_table} p ON p.id = t.{token_parent_column}"]
    speaker_parts = ["p.speaker_id"] if "speaker_id" in parent_columns else []
    if "speakers" in tables and "speaker_id" in parent_columns:
        speaker_columns = _columns(conn, "speakers")
        joins.append("LEFT JOIN speakers sp ON sp.id = p.speaker_id")
        speaker_parts = [f"sp.{column}" for column in ("label", "display_name", "participant_code") if column in speaker_columns] + speaker_parts
    scene_parts = ["p.scene_id"] if "scene_id" in parent_columns else []
    if "scenes" in tables and "scene_id" in parent_columns:
        scene_columns = _columns(conn, "scenes")
        joins.append("LEFT JOIN scenes sc ON sc.id = p.scene_id")
        scene_parts = [f"sc.{column}" for column in ("name", "label") if column in scene_columns] + scene_parts
    language_parts = ["t.language"] if "language" in token_columns else []
    if "annotations" in tables and "token_id" in annotation_columns and "language_id" in annotation_columns:
        status_clause = " AND ann.status = 'active'" if "status" in annotation_columns else ""
        joins.append(f"LEFT JOIN annotations ann ON ann.token_id = t.id{status_clause}")
        language_parts.insert(0, "ann.language_id")
        if "languages" in tables and "id" in language_columns and "code" in language_columns:
            joins.append("LEFT JOIN languages lang ON lang.id = ann.language_id")
            language_parts.insert(0, "lang.code")
    position_expr = "t.sort_order" if "sort_order" in token_columns else ("t.position" if "position" in token_columns else "0")
    parent_order_expr = "p.sort_order" if "sort_order" in parent_columns else ("p.position" if "position" in parent_columns else "0")
    start_expr = "p.start_ms" if "start_ms" in parent_columns else ("p.start_time_ms" if "start_time_ms" in parent_columns else "NULL")
    query = f"""
        SELECT
            t.id AS token_id,
            {position_expr} AS position,
            {_coalesce(speaker_parts, "'unknown'")} AS speaker,
            {_coalesce(scene_parts, "'scene_unknown'")} AS scene,
            {_coalesce(language_parts, "'und'")} AS language,
            {start_expr} AS start_time_ms
        FROM tokens t
        {' '.join(joins)}
        ORDER BY speaker, scene, {parent_order_expr}, {position_expr}
    """
    return [
        TokenObservation(
            token_id=str(row["token_id"]),
            speaker=str(row["speaker"] or "unknown"),
            scene=str(row["scene"] or "scene_unknown"),
            language=str(row["language"] or "und"),
            position=int(row["position"] or 0),
            start_time_ms=int(row["start_time_ms"]) if row["start_time_ms"] is not None else None,
        )
        for row in conn.execute(query).fetchall()
    ]


def _observations_from_token_table(conn: sqlite3.Connection) -> list[TokenObservation]:
    token_columns = _columns(conn, "tokens")
    position_expr = "sort_order" if "sort_order" in token_columns else ("position" if "position" in token_columns else "0")
    speaker_expr = "speaker_id" if "speaker_id" in token_columns else "'unknown'"
    scene_expr = "scene" if "scene" in token_columns else ("scene_id" if "scene_id" in token_columns else "'scene_unknown'")
    language_expr = "language" if "language" in token_columns else "'und'"
    start_expr = "start_ms" if "start_ms" in token_columns else ("start_time_ms" if "start_time_ms" in token_columns else "NULL")
    query = f"""
        SELECT id AS token_id,
               {position_expr} AS position,
               {speaker_expr} AS speaker,
               {scene_expr} AS scene,
               {language_expr} AS language,
               {start_expr} AS start_time_ms
        FROM tokens
        ORDER BY speaker, scene, {position_expr}, id
    """
    return [
        TokenObservation(
            token_id=str(row["token_id"]),
            speaker=str(row["speaker"] or "unknown"),
            scene=str(row["scene"] or "scene_unknown"),
            language=str(row["language"] or "und"),
            position=int(row["position"] or 0),
            start_time_ms=int(row["start_time_ms"]) if row["start_time_ms"] is not None else None,
        )
        for row in conn.execute(query).fetchall()
    ]


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _coalesce(parts: list[str], fallback: str) -> str:
    return f"COALESCE({', '.join(parts)}, {fallback})" if parts else fallback


def _observations_from_tokens(tokens: list[Token]) -> list[TokenObservation]:
    observations: list[TokenObservation] = []
    for token in tokens:
        metadata = token.metadata or {}
        observations.append(
            TokenObservation(
                token_id=token.id,
                speaker=token.speaker_id or str(metadata.get("speaker", "unknown")),
                scene=str(metadata.get("scene", metadata.get("scene_id", "scene_unknown"))),
                language=token.language or "und",
                position=token.position,
                start_time_ms=int(metadata["start_time_ms"]) if metadata.get("start_time_ms") is not None else None,
            )
        )
    return observations


def _database_path(project: Project) -> Path | None:
    paths = getattr(project, "paths", None)
    if paths is not None and getattr(paths, "database", None):
        return Path(str(paths.database))
    database_path = _metadata_value(project, "database_path")
    if database_path:
        return Path(str(database_path))
    if getattr(project, "project_path", None):
        root = Path(str(project.project_path))
        return root if root.name.endswith(".sqlite") else root / "project.sqlite"
    return None


def _project_root(project: Project) -> Path | None:
    if getattr(project, "project_path", None):
        return Path(str(project.project_path))
    paths = getattr(project, "paths", None)
    if paths is not None and getattr(paths, "root", None):
        return Path(str(paths.root))
    database = _database_path(project)
    return database.parent if database else None


def _axes(cells: list[HeatmapCell]) -> tuple[list[str], list[str]]:
    speakers = sorted({cell.speaker for cell in cells}) or ["unknown"]
    scenes = sorted({cell.scene for cell in cells}) or ["scene_unknown"]
    return speakers, scenes


def _footer(project: Project) -> str:
    dictionaries = _metadata_value(project, "dictionary_versions", {})
    dictionary_text = ", ".join(f"{k}={v}" for k, v in sorted(dictionaries.items())) if dictionaries else "dictionary versions unavailable"
    title = getattr(project, "title", None) or _metadata_value(project, "title", "Imbizo-CS project")
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    return f"{title} | generated {timestamp} | Imbizo-CS {__version__} | {dictionary_text} | see PRINCIPLES.md"


def _metadata_value(project: Project, key: str, default: Any = None) -> Any:
    """Read metadata values from dict-backed or dataclass-backed projects."""

    metadata = getattr(project, "metadata", None)
    if isinstance(metadata, dict):
        return metadata.get(key, default)
    return getattr(metadata, key, default)


def _save_figure(fig: Any, output_path: Path, format: str, title: str, desc: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format=format, dpi=160, metadata={"Title": title, "Description": desc})
    import matplotlib.pyplot as plt

    plt.close(fig)
    if format == "svg":
        _inject_svg_accessibility(output_path, title, desc)


def _inject_svg_accessibility(path: Path, title: str, desc: str) -> None:
    text = path.read_text(encoding="utf-8")
    if "role=\"img\"" not in text:
        text = text.replace("<svg ", f"<svg role=\"img\" aria-label=\"{_escape_xml(title)}\" ", 1)
    inserts = ""
    if "<title>" not in text:
        inserts += f"<title>{_escape_xml(title)}</title>"
    if "<desc>" not in text:
        inserts += f"<desc>{_escape_xml(desc)}</desc>"
    if inserts:
        index = text.find(">", text.find("<svg"))
        if index != -1:
            text = text[: index + 1] + inserts + text[index + 1 :]
    path.write_text(text, encoding="utf-8")


def _escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
