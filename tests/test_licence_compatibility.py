"""Tests for tiered resource licence compatibility controls."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import yaml
from click.testing import CliRunner
from jinja2 import Environment, FileSystemLoader

from imbizo.core.licence import registry
from tools import bootstrap
from tools.check_compliance import _check_licence_classification


def test_manifest_licence_classification_blocks_parse() -> None:
    """Every bootstrap source declares the licence tier metadata."""

    manifest = yaml.safe_load(Path("bootstrap/sources.yaml").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == "1.1"
    for source in manifest["sources"]:
        classification = source.get("licence_classification")
        assert isinstance(classification, dict), source["id"]
        assert classification["tier"] in {1, 2, 3}, source["id"]
        assert classification["combinable_with_agpl"] in {"combination", "aggregation_only", "none"}
        assert classification["redistribution_notice"].strip()


def test_has_nc_resources_detects_fixture(monkeypatch, tmp_path: Path) -> None:
    """The runtime registry detects active Tier-2 NC resources."""

    resource_dir = tmp_path / "corpora" / "masakhapos"
    resource_dir.mkdir(parents=True)
    (resource_dir / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "dictionary_kind": "processing_resource",
                "source": {
                    "origin_name": "MasakhaPOS",
                    "origin_license": "CC-BY-NC-4.0",
                    "licence_classification": {
                        "spdx_id": "CC-BY-NC-4.0",
                        "tier": 2,
                        "fosl_compatible": False,
                        "combinable_with_agpl": "aggregation_only",
                        "commercial_use_restricted": True,
                        "sharealike_required": False,
                        "downstream_obligations": ["attribution", "non_commercial"],
                        "redistribution_notice": "NC notice",
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "SCAN_ROOTS", (tmp_path,))
    assert registry.has_nc_resources() is True


def test_bootstrap_refuses_tier2_without_env(tmp_path: Path) -> None:
    """Tier-2 opt-in requires IMBIZO_NC_ACCEPTED=1."""

    manifest = _manifest(tmp_path, tier=2)
    result = CliRunner().invoke(
        bootstrap.main,
        ["--manifest", str(manifest), "--include-nc-data"],
        env={"IMBIZO_NC_ACCEPTED": ""},
    )
    assert result.exit_code != 0
    assert "IMBIZO_NC_ACCEPTED=1" in result.output


def test_bootstrap_refuses_tier3_without_env(tmp_path: Path) -> None:
    """Tier-3 opt-in requires IMBIZO_COMMUNITY_ACCEPTED=1."""

    manifest = _manifest(tmp_path, tier=3)
    result = CliRunner().invoke(
        bootstrap.main,
        ["--manifest", str(manifest), "--include-community"],
        env={"IMBIZO_COMMUNITY_ACCEPTED": ""},
    )
    assert result.exit_code != 0
    assert "IMBIZO_COMMUNITY_ACCEPTED=1" in result.output


def test_licence_propagation_partial_renders_notice() -> None:
    """The report partial emits verbatim Tier-2 notices."""

    templates_root = Path("src/imbizo/resources/templates")
    env = Environment(loader=FileSystemLoader(str(templates_root)), autoescape=True)
    template = env.get_template("partials/licence_propagation.html.j2")
    classification = SimpleNamespace(spdx_id="CC-BY-NC-4.0", tier=2, combinable_with_agpl="aggregation_only")
    resource = SimpleNamespace(resource_name="MasakhaPOS", classification=classification)
    report = SimpleNamespace(
        has_obligations=True,
        resources=(resource,),
        nc_resources=(resource,),
        sharealike_resources=(),
        notices=("MasakhaPOS NC notice",),
    )
    rendered = template.render(licence_report=report)
    assert "MasakhaPOS NC notice" in rendered
    assert "NonCommercial notice" in rendered


def test_compliance_fails_tier2_without_notice(tmp_path: Path) -> None:
    """Tier-2 metadata must include redistribution_notice."""

    failures = _check_licence_classification(
        tmp_path / "bad.yaml",
        {
            "licence_classification": {
                "spdx_id": "CC-BY-NC-4.0",
                "tier": 2,
                "fosl_compatible": False,
                "combinable_with_agpl": "aggregation_only",
                "commercial_use_restricted": True,
                "sharealike_required": False,
                "downstream_obligations": ["non_commercial"],
                "redistribution_notice": "",
            }
        },
    )
    assert any("redistribution_notice" in failure for failure in failures)


def test_core_modules_do_not_import_network_libraries() -> None:
    """The licence registry does not weaken the runtime offline boundary."""

    forbidden = {"urllib.request", "requests", "httpx", "aiohttp", "socket"}
    offenders: list[str] = []
    for path in sorted(Path("src/imbizo/core").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders.extend(alias.name for alias in node.names if alias.name in forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module in forbidden:
                offenders.append(node.module)
    assert not offenders


def _manifest(tmp_path: Path, tier: int) -> Path:
    manifest = tmp_path / "sources.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "manifest_version": "1.1",
                "sources": [
                    {
                        "id": f"tier{tier}_fixture",
                        "name": "fixture",
                        "url": "https://example.invalid/resource.txt",
                        "format": "txt",
                        "license": "CC-BY-NC-4.0" if tier == 2 else "NOODL-1.0",
                        "licence_classification": {
                            "spdx_id": "CC-BY-NC-4.0" if tier == 2 else "NOODL-1.0",
                            "tier": tier,
                            "fosl_compatible": False,
                            "combinable_with_agpl": "aggregation_only",
                            "commercial_use_restricted": tier == 2,
                            "sharealike_required": False,
                            "downstream_obligations": ["attribution"],
                            "redistribution_notice": f"Tier {tier} notice",
                        },
                        "license_check_required": False,
                        "expected_sha256": None,
                        "bundle_status": "shippable",
                        "adapter": "tools/adapters/up_lexicons.py",
                        "output_dirs": ["dictionaries/imported/base_lexicon"],
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return manifest
