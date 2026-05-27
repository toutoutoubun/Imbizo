from pathlib import Path

from imbizo.core.annotation import Project, Token
from imbizo.core.visualisation.heatmap import load_token_observations
from imbizo.core.visualisation.sankey import compute_language_transition_flows, render_language_transition_sankey


def _project(tmp_path: Path) -> Project:
    tokens = [
        Token("t1", "a", "u1", 1, "zul", speaker_id="S1", metadata={"scene": "A", "start_time_ms": 1}),
        Token("t2", "b", "u1", 2, "eng", speaker_id="S1", metadata={"scene": "A", "start_time_ms": 2}),
        Token("t3", "c", "u1", 3, "zul", speaker_id="S1", metadata={"scene": "A", "start_time_ms": 3}),
        Token("t4", "d", "u2", 1, "eng", speaker_id="S2", metadata={"scene": "B", "start_time_ms": 4}),
        Token("t5", "e", "u2", 2, "zul", speaker_id="S2", metadata={"scene": "B", "start_time_ms": 5}),
    ]
    return Project("p", "Synthetic", tokens, project_path=str(tmp_path))


def test_sankey_file_creation_and_accessible_svg(tmp_path: Path) -> None:
    path = render_language_transition_sankey(_project(tmp_path), tmp_path / "sankey.svg")
    assert isinstance(path, Path)
    text = path.read_text(encoding="utf-8")
    assert "<title>" in text
    assert "<desc>" in text


def test_flow_counts_are_proportional_input(tmp_path: Path) -> None:
    flows = compute_language_transition_flows(load_token_observations(_project(tmp_path)))
    counts = {(flow.source, flow.target): flow.count for flow in flows}
    assert counts[("eng", "zul")] == 2
    assert counts[("zul", "eng")] == 1


def test_per_speaker_mode_outputs_two_files(tmp_path: Path) -> None:
    paths = render_language_transition_sankey(_project(tmp_path), tmp_path / "sankey.svg", per_speaker=True)
    assert isinstance(paths, list)
    assert len(paths) == 2
    assert all(path.exists() for path in paths)
