import json
from pathlib import Path

from app.eval.cli import main

ROOT = Path(__file__).resolve().parents[2] / "samples"


def test_cli_runs_on_sample_corpus(tmp_path, capsys):
    out = tmp_path / "report.json"
    assert main(["--corpus", str(ROOT / "corpus"), "--dataset", str(ROOT / "eval.jsonl"),
                 "--k", "3", "--json", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "| bm25 |" in printed and "hybrid+rerank+expand" in printed
    report = json.loads(out.read_text())
    assert len(report["retrieval"]) == 5
    best = report["retrieval"][3]["metrics"]
    assert best["hit@k"] >= 0.9  # regression guard for the default pipeline


def test_cli_lists_failures(capsys):
    main(["--corpus", str(ROOT / "corpus"), "--dataset", str(ROOT / "eval.jsonl"),
          "--failures"])
    assert "missed rank 1" in capsys.readouterr().out


def test_cli_sweep_prints_one_row_per_size(capsys):
    main(["--corpus", str(ROOT / "corpus"), "--dataset", str(ROOT / "eval.jsonl"), "--sweep"])
    out = capsys.readouterr().out
    assert out.count("| size=") == 6
