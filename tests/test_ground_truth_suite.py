from __future__ import annotations

import json
from pathlib import Path

from witnis.core.ground_truth import evaluate_case, load_label, run_ground_truth_suite

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "benchmarks" / "ground-truth" / "labels"
PETCLINIC = (
    ROOT
    / "benchmarks"
    / "ground-truth"
    / "corpora"
    / "checkouts"
    / "spring-petclinic"
)


def test_ground_truth_vendored_fixtures(tmp_path: Path) -> None:
    """CI acceptance: only vendored semantic_* labels must stay perfect."""
    vendored = tmp_path / "vendored"
    vendored.mkdir()
    for name in ("semantic_java_di.json", "semantic_py_di.json"):
        src = LABELS / name
        (vendored / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    report = run_ground_truth_suite(
        labels_dir=vendored,
        repo_root=ROOT,
        work_dir=tmp_path / "work",
    )
    assert report["cases"] >= 1
    assert report["fn"] == 0, report
    assert (report.get("recall") or 0) >= 0.99


def test_petclinic_human_labels_load_and_score(tmp_path: Path) -> None:
    human = LABELS / "spring_petclinic_human.json"
    assert human.is_file()
    label = load_label(human)
    assert label["label_mode"] == "human_v2_adjudicated"
    assert "human-v2-adjudication" in label["annotators"]
    assert len(label["tasks"]) >= 18
    assert label["commit"].startswith("500158f")

    if not PETCLINIC.is_dir():
        # Checkout is gitignored; suite must skip rather than fail CI.
        report = run_ground_truth_suite(
            labels_dir=LABELS,
            repo_root=ROOT,
            work_dir=tmp_path,
        )
        human_rep = next(r for r in report["reports"] if r.get("case_id") == "spring_petclinic_human")
        assert human_rep.get("status") == "skipped"
        return

    rep = evaluate_case(label, PETCLINIC, tmp_path / "petclinic-human.sqlite")
    metrics = {m.name: m for m in rep.metrics}
    data = rep.as_dict()
    failed = [t["id"] for t in data["tasks"] if not t.get("ok")]
    assert failed == [], data["tasks"]
    assert metrics["call_edge"].tp >= 6
    assert metrics["impact_direct"].tp >= 3
    assert metrics["impact_indirect"].tp >= 3
    assert (metrics["impact_indirect"].recall or 0) >= 0.99
    assert "expected_item_recall" in str(data.get("scoring") or "")
    person = next(t for t in data["tasks"] if t.get("id") == "h_impact_person")
    assert person.get("ok") is True
    (tmp_path / "petclinic-human-report.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
