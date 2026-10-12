import csv
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))
import triage as t  # noqa: E402

SAMPLES = Path(__file__).parent.parent / "sample_emails"


def test_eml_parsing():
    mails = t.load_folder(SAMPLES)
    assert len(mails) >= 6
    m = next(m for m in mails if m.id == "03_billing")
    assert m.subject.startswith("Charged twice")
    assert "priya@kestrel-design.example" in m.sender
    assert "INV-20931" in m.body


def test_dry_run_classifier():
    by_id = {m.id: t.classify_dry_run(m) for m in t.load_folder(SAMPLES)}
    assert by_id["04_spam"].category == "spam" and by_id["04_spam"].reply_draft == ""
    assert by_id["03_billing"].category == "billing"
    assert by_id["02_support_urgent"].category == "support"
    assert by_id["02_support_urgent"].priority == "high"
    assert by_id["02_support_urgent"].sentiment == "negative"
    assert by_id["01_sales_lead"].category == "sales_lead"


GOOD = dict(category="support", priority="high", sentiment="negative", customer_name="Tom",
            company="Northfield", requested_action="Restore access", deadline="today 3pm",
            reply_draft="Hi Tom, we are on it.")


def test_mocked_claude_response():
    calls = []

    class FakeMessages:
        def parse(self, **kw):
            calls.append(kw)
            return SimpleNamespace(parsed_output=t.Triage(**GOOD), stop_reason="end_turn")

    client = SimpleNamespace(messages=FakeMessages())
    mail = t.Email("x", "a@b.example", "Down", "Login broken")
    result = t.classify_ai(client, mail)
    assert result.priority == "high"
    assert calls[0]["output_format"] is t.Triage and calls[0]["model"] == t.MODEL


def test_missing_structured_output_raises():
    client = SimpleNamespace(messages=SimpleNamespace(
        parse=lambda **kw: SimpleNamespace(parsed_output=None, stop_reason="refusal")))
    with pytest.raises(ValueError):
        t.classify_ai(client, t.Email("x", "a", "b", "c"))


def test_invalid_response_rejected():
    with pytest.raises(ValidationError):
        t.Triage(**{**GOOD, "category": "urgent-stuff"})


def test_csv_and_drafts(tmp_path):
    mails = t.load_folder(SAMPLES)
    rows = [(m, t.classify_dry_run(m)) for m in mails]
    t.write_csv(rows, tmp_path / "out.csv")
    t.write_drafts(rows, tmp_path / "drafts")
    data = list(csv.DictReader(open(tmp_path / "out.csv", encoding="utf-8")))
    assert len(data) == len(mails) and data[0]["category"]
    assert not (tmp_path / "drafts" / "04_spam.txt").exists()
    assert (tmp_path / "drafts" / "03_billing.txt").exists()


def test_cli_dry_run(tmp_path):
    assert t.main([str(SAMPLES), "--dry-run", "-o", str(tmp_path / "o.csv"),
                   "--drafts-dir", str(tmp_path / "d")]) == 0
    assert (tmp_path / "o.csv").exists()
