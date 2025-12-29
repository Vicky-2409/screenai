from types import SimpleNamespace

from app.services import matching


def test_strip_html_removes_tags_and_entities():
    html = "<p>Build <b>scalable</b> APIs &amp; services</p><ul><li>Python</li></ul>"
    out = matching.strip_html(html)
    assert "<" not in out and ">" not in out
    assert "Build scalable APIs & services" in out
    assert "Python" in out


def test_strip_html_handles_none_and_empty():
    assert matching.strip_html(None) == ""
    assert matching.strip_html("") == ""


def test_build_job_text_uses_clean_text():
    job = SimpleNamespace(
        title="Backend Engineer",
        department="Engineering",
        description="<p>Build <b>APIs</b></p>",
        responsibilities="<ul><li>Design REST</li></ul>",
        qualifications="<p>Bachelor degree</p>",
        skills=["python", "fastapi"],
    )
    text = matching.build_job_text(job)
    assert "<" not in text
    assert "Build APIs" in text
    assert "Design REST" in text
    assert "Bachelor degree" in text
    assert "python" in text
