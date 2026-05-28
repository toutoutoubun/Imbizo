"""Offline language-transition Sankey rendering with pure matplotlib.

This module renders static polygon ribbons instead of depending on a web-based
diagramming library. Widths are proportional to transition counts, language
labels are present at both ends, and each flow has a glyph marker so meaning is
not encoded in colour alone.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from imbizo.core.annotation import Project

from .heatmap import TokenObservation, _escape_xml, _footer, load_token_observations
from .palette import LanguagePalette


@dataclass(slots=True)
class LanguageFlow:
    """One source-to-target language transition."""

    source: str
    target: str
    count: int
    speaker: str | None = None


def render_language_transition_sankey(
    project: Project,
    output_path: Path,
    time_window: Literal["utterance", "clause", "token"] = "utterance",
    format: Literal["png", "svg"] = "svg",
    per_speaker: bool = False,
) -> Path | list[Path]:
    """Render language transition flows as a local Sankey-style diagram."""

    if format not in {"png", "svg"}:
        raise ValueError("format must be 'png' or 'svg'.")
    if time_window not in {"utterance", "clause", "token"}:
        raise ValueError("time_window must be utterance, clause, or token.")
    observations = load_token_observations(project)
    if per_speaker:
        paths: list[Path] = []
        speakers = sorted({obs.speaker for obs in observations}) or ["unknown"]
        for speaker in speakers:
            flows = compute_language_transition_flows([obs for obs in observations if obs.speaker == speaker], time_window, speaker=speaker)
            target = output_path.with_name(f"{output_path.stem}_{_safe_name(speaker)}.{format}")
            _render_flows(flows, target, format, project, f"Language transitions for {speaker}")
            paths.append(target)
        return paths
    flows = compute_language_transition_flows(observations, time_window)
    _render_flows(flows, output_path, format, project, "Language transition Sankey")
    return output_path


def compute_language_transition_flows(
    observations: list[TokenObservation],
    time_window: Literal["utterance", "clause", "token"] = "utterance",
    *,
    speaker: str | None = None,
) -> list[LanguageFlow]:
    """Compute adjacent language transitions from ordered token observations."""

    if not observations:
        return []
    ordered = sorted(observations, key=lambda obs: ((obs.start_time_ms or 0), obs.speaker, obs.scene, obs.position, obs.token_id))
    if time_window == "token":
        groups = {"all": ordered}
    else:
        groups: dict[str, list[TokenObservation]] = defaultdict(list)
        for obs in ordered:
            key = f"{obs.speaker}:{obs.scene}" if time_window == "utterance" else f"{obs.speaker}:{obs.scene}:{obs.start_time_ms or 0}"
            groups[key].append(obs)
    counts: Counter[tuple[str, str]] = Counter()
    for group in groups.values():
        previous = None
        for obs in sorted(group, key=lambda item: (item.start_time_ms or 0, item.position, item.token_id)):
            language = obs.language or "und"
            if previous and language != previous:
                counts[(previous, language)] += 1
            previous = language
    return [LanguageFlow(source=src, target=tgt, count=count, speaker=speaker) for (src, tgt), count in sorted(counts.items())]


def _render_flows(flows: list[LanguageFlow], output_path: Path, format: str, project: Project, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch

    matplotlib.rcParams["svg.fonttype"] = "path"
    palette = LanguagePalette()
    languages = sorted({flow.source for flow in flows} | {flow.target for flow in flows}) or ["und"]
    total = sum(flow.count for flow in flows) or 1
    fig, ax = plt.subplots(figsize=(9, max(4, len(languages) * 0.7 + 1.5)), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title)
    source_y = _positions(languages)
    target_y = _positions(languages)
    source_offsets = {language: 0.0 for language in languages}
    target_offsets = {language: 0.0 for language in languages}
    max_width = 0.28
    for flow in sorted(flows, key=lambda item: item.count, reverse=True):
        width = max(0.018, max_width * flow.count / total)
        y0 = source_y[flow.source] + source_offsets[flow.source]
        y1 = target_y[flow.target] + target_offsets[flow.target]
        source_offsets[flow.source] += width * 0.55
        target_offsets[flow.target] += width * 0.55
        path = MplPath(
            [(0.18, y0 - width / 2), (0.40, y0 - width / 2), (0.60, y1 - width / 2), (0.82, y1 - width / 2),
             (0.82, y1 + width / 2), (0.60, y1 + width / 2), (0.40, y0 + width / 2), (0.18, y0 + width / 2), (0.18, y0 - width / 2)],
            [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY],
        )
        patch = PathPatch(path, facecolor=palette.colour_for(flow.source), alpha=0.62, edgecolor="#333333", linewidth=0.5)
        ax.add_patch(patch)
        ax.text(0.50, (y0 + y1) / 2, str(flow.count), ha="center", va="center", fontsize=8)
    for language in languages:
        ax.text(0.04, source_y[language], f"{palette.glyph_for(language)} {language}", ha="left", va="center", fontsize=10)
        ax.text(0.96, target_y[language], f"{language} {palette.glyph_for(language)}", ha="right", va="center", fontsize=10)
        ax.plot([0.16], [source_y[language]], marker="o", color=palette.colour_for(language), markersize=8)
        ax.plot([0.84], [target_y[language]], marker="s", color=palette.colour_for(language), markersize=8)
    fig.text(0.01, 0.01, _footer(project), fontsize=7, ha="left")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format=format, dpi=160, metadata={"Title": title, "Description": "Language transition Sankey diagram"})
    plt.close(fig)
    if format == "svg":
        _inject_sankey_svg_accessibility(output_path, title)


def _positions(languages: list[str]) -> dict[str, float]:
    if len(languages) == 1:
        return {languages[0]: 0.5}
    step = 0.78 / (len(languages) - 1)
    return {language: 0.89 - index * step for index, language in enumerate(languages)}


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_") or "speaker"


def _inject_sankey_svg_accessibility(path: Path, title: str) -> None:
    text = path.read_text(encoding="utf-8")
    desc = "Sankey diagram of local code-switch language transitions."
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
