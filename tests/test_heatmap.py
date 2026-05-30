from pathlib import Path
import sqlite3

from imbizo.core.annotation import Project, Token
from imbizo.core.visualisation.heatmap import compute_speaker_scene_language_proportions, load_token_observations, render_speaker_scene_heatmap
from imbizo.core.visualisation.palette import LanguagePalette
from imbizo.domain.project import ProjectContext, ProjectMetadata, ProjectPaths


def _project(tmp_path: Path) -> Project:
    return Project(
        id="p1",
        title="Synthetic",
        project_path=str(tmp_path),
        metadata={"dictionary_versions": {"zul": "0.1.0"}},
        tokens=[
            Token("t1", "ngi", "u1", 1, "zul", speaker_id="S1", metadata={"scene": "interview"}),
            Token("t2", "work", "u1", 2, "eng", speaker_id="S1", metadata={"scene": "interview"}),
            Token("t3", "sawubona", "u2", 1, "zul", speaker_id="S2", metadata={"scene": "aside"}),
        ],
    )


def test_heatmap_file_created(tmp_path: Path) -> None:
    path = render_speaker_scene_heatmap(_project(tmp_path), tmp_path / "heatmap.png")
    assert isinstance(path, Path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_heatmap_cell_counts_match_input(tmp_path: Path) -> None:
    cells = compute_speaker_scene_language_proportions(load_token_observations(_project(tmp_path)))
    cell = next(item for item in cells if item.speaker == "S1" and item.scene == "interview")
    assert cell.total_tokens == 2
    assert cell.proportions["zul"] == 0.5
    assert cell.proportions["eng"] == 0.5


def test_colourblind_safe_palette_flag() -> None:
    assert LanguagePalette().is_colourblind_safe()


def test_per_language_heatmaps(tmp_path: Path) -> None:
    paths = render_speaker_scene_heatmap(_project(tmp_path), tmp_path / "heatmap.svg", format="svg", per_language=True)
    assert isinstance(paths, list)
    assert {path.suffix for path in paths} == {".svg"}


def test_load_token_observations_supports_utterances_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "project.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE utterances (id TEXT PRIMARY KEY, speaker_id TEXT, scene_id TEXT, sort_order INTEGER, start_time_ms INTEGER)"
    )
    conn.execute(
        "CREATE TABLE tokens (id TEXT PRIMARY KEY, utterance_id TEXT, sort_order INTEGER, language TEXT)"
    )
    conn.execute("INSERT INTO utterances VALUES ('u1', 'S1', 'sceneA', 1, 100)")
    conn.execute("INSERT INTO tokens VALUES ('t1', 'u1', 1, 'zul')")
    conn.commit()
    conn.close()
    observations = load_token_observations(Project("p", "SQLite Project", [], metadata={"database_path": str(db_path)}))
    assert len(observations) == 1
    assert observations[0].speaker == "S1"
    assert observations[0].scene == "sceneA"
    assert observations[0].language == "zul"


def test_heatmap_accepts_project_context_metadata_dataclass(tmp_path: Path) -> None:
    """GUI dashboard passes ProjectContext with dataclass metadata, not a dict."""

    paths = ProjectPaths.from_root(tmp_path / "project")
    paths.ensure_all()
    conn = sqlite3.connect(paths.database)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE segments (id TEXT PRIMARY KEY, speaker_id TEXT, scene_id TEXT, sort_order INTEGER)")
    conn.execute("CREATE TABLE tokens (id TEXT PRIMARY KEY, segment_id TEXT, sort_order INTEGER, language TEXT)")
    conn.execute("INSERT INTO segments VALUES ('s1', 'S1', 'sceneA', 1)")
    conn.execute("INSERT INTO tokens VALUES ('t1', 's1', 1, 'eng')")
    conn.commit()
    context = ProjectContext(
        paths=paths,
        metadata=ProjectMetadata(project_uuid="p1", title="Dataclass Metadata Project"),
        connection=conn,
    )

    path = render_speaker_scene_heatmap(context, paths.exports / "figures" / "heatmap.png")  # type: ignore[arg-type]

    assert isinstance(path, Path)
    assert path.exists()
    assert path.stat().st_size > 0
    conn.close()
