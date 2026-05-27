"""WeasyPrint PDF rendering for self-contained local HTML reports.

The renderer accepts only local templates and rejects HTTP(S) resource fetches.
This preserves the offline-first and data-sovereignty guarantees while allowing
print-quality PDF output for reports that cite code-switching and 4-M analyses
(Poplack, 1980; Muysken, 2000; Myers-Scotton, 2002).
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from imbizo.core.licence.registry import downstream_propagation_summary


def render_report_to_pdf(template_name: str, context: dict, out_path: Path) -> None:
    """Render a bundled Jinja2 report template to a local PDF file.

    The function performs no network calls. It loads templates from
    `imbizo.resources.templates`, renders them with Jinja2, and passes the
    resulting self-contained HTML to WeasyPrint with a URL fetcher that rejects
    remote HTTP and HTTPS resources.
    """

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        from weasyprint import HTML, default_url_fetcher
    except ImportError as exc:
        raise RuntimeError(
            "PDF rendering requires locally installed Jinja2 and WeasyPrint. "
            "Install them from the offline wheelhouse; no internet access is required at runtime."
        ) from exc

    templates_root = resources.files("imbizo") / "resources" / "templates"
    with resources.as_file(templates_root) as template_dir:
        environment = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(("html", "xml", "j2")),
        )
        render_context = dict(context)
        render_context.setdefault("licence_report", downstream_propagation_summary())
        template = environment.get_template(template_name)
        html_text = template.render(**render_context)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(
            string=html_text,
            base_url=str(template_dir),
            url_fetcher=_local_only_url_fetcher(default_url_fetcher),
        ).write_pdf(out_path)


def _local_only_url_fetcher(default_fetcher: Any) -> Any:
    """Return a WeasyPrint URL fetcher that rejects remote resources."""

    def fetch(url: str) -> Any:
        if url.startswith(("http://", "https://")):
            raise RuntimeError(f"Remote resources are not allowed in offline reports: {url}")
        return default_fetcher(url)

    return fetch
