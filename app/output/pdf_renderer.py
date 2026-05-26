from weasyprint import HTML, CSS
from app.schemas.report import FinalReport


_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a1a;
    padding: 48pt 60pt;
}

h1 {
    font-size: 20pt;
    font-weight: 600;
    color: #111;
    margin-bottom: 6pt;
}

.meta {
    font-size: 9pt;
    color: #666;
    margin-bottom: 24pt;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 12pt;
}

h2 {
    font-size: 13pt;
    font-weight: 600;
    color: #222;
    margin-top: 24pt;
    margin-bottom: 8pt;
}

p {
    margin-bottom: 10pt;
}

.executive-summary {
    background: #f7f7f7;
    border-left: 3px solid #555;
    padding: 12pt 16pt;
    margin-bottom: 24pt;
    font-size: 10.5pt;
    color: #333;
}

.citations {
    margin-top: 32pt;
    border-top: 1px solid #e0e0e0;
    padding-top: 16pt;
}

.citations h2 {
    font-size: 11pt;
    color: #444;
    margin-bottom: 8pt;
}

.citations ul {
    list-style: none;
    padding: 0;
}

.citations li {
    font-size: 9pt;
    color: #555;
    margin-bottom: 4pt;
}

.eval-block {
    margin-top: 32pt;
    border-top: 1px solid #e0e0e0;
    padding-top: 16pt;
    font-size: 9pt;
    color: #666;
}

.eval-block table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 8pt;
}

.eval-block th, .eval-block td {
    text-align: left;
    padding: 4pt 8pt;
    border-bottom: 1px solid #eee;
}

.eval-block th {
    font-weight: 500;
    color: #444;
}

@page {
    margin: 0;
    size: A4;
}
"""


def _build_html(report: FinalReport) -> str:
    sections_html = ""
    for section in report.sections:
        content_paragraphs = "".join(
            f"<p>{para.strip()}</p>"
            for para in section.content.split("\n\n")
            if para.strip()
        )
        sections_html += f"<h2>{section.heading}</h2>{content_paragraphs}"

    citations_html = "".join(
        f"<li>{c.source} (relevance: {c.relevance_score})</li>"
        for c in report.citations
    )

    dimension_rows = "".join(
        f"<tr><td>{d['dimension']}</td><td>{d['score']}/5.0</td>"
        f"<td>{d.get('feedback', '')}</td></tr>"
        for d in report.evaluation.get("dimension_scores", [])
    )

    passed_label = "Passed" if report.evaluation.get("passed") else "Did not pass"

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{report.title}</title></head>
<body>
  <h1>{report.title}</h1>
  <div class="meta">
    Generated: {report.generated_at} &nbsp;|&nbsp;
    Revisions: {report.metadata.get('revision_count', 0)} &nbsp;|&nbsp;
    Score: {report.evaluation.get('overall_score', 0.0)}/5.0 &nbsp;|&nbsp;
    {passed_label}
  </div>

  <div class="executive-summary">
    {report.executive_summary}
  </div>

  {sections_html}

  <div class="citations">
    <h2>Sources</h2>
    <ul>{citations_html}</ul>
  </div>

  <div class="eval-block">
    <h2>Evaluation breakdown</h2>
    <table>
      <tr><th>Dimension</th><th>Score</th><th>Feedback</th></tr>
      {dimension_rows}
    </table>
  </div>
</body>
</html>"""


def render_to_pdf(report: FinalReport, output_path: str) -> str:
    """
    Renders a FinalReport to a PDF file at output_path.
    Returns the output path on success.
    """
    html_content = _build_html(report)
    HTML(string=html_content).write_pdf(
        output_path,
        stylesheets=[CSS(string=_BASE_CSS)],
    )
    return output_path


def render_to_bytes(report: FinalReport) -> bytes:
    """
    Renders a FinalReport to PDF bytes without writing to disk.
    Used for returning PDF directly from the API as a streaming response.
    """
    html_content = _build_html(report)
    return HTML(string=html_content).write_pdf(
        stylesheets=[CSS(string=_BASE_CSS)],
    )