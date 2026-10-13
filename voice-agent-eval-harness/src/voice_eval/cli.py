"""Command-line interface: `uv run voice-eval --help`."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from voice_eval.config import (
    ANNOTATION_TEMPLATE_PATH,
    HUMAN_ANNOTATIONS_PATH,
    ROOT,
    TRANSCRIPTS_PATH,
    load_experiment_defaults,
    rel,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Voice Agent Evaluation Harness — BFSI Collections Benchmark",
)

RubricOpt = Annotated[str, typer.Option("--rubric", "-r", help="Rubric version, e.g. v1")]


def _ids(raw: str | None) -> list[str] | None:
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else None


# -------------------------------------------------------------------------------- dataset
@app.command("generate-dataset")
def generate_dataset_cmd(
    force: Annotated[
        bool, typer.Option(help="Overwrite a differing frozen dataset (new version only).")
    ] = False,
    verify: Annotated[
        bool, typer.Option(help="Only check that the committed file is reproducible.")
    ] = False,
) -> None:
    """Generate the 100 deterministic synthetic transcripts (refuses to silently overwrite)."""
    from voice_eval.generation import FrozenDatasetError, verify_reproducible, write_dataset

    if verify:
        ok = verify_reproducible()
        typer.echo(
            "Reproducible: committed dataset matches a fresh generation."
            if ok
            else "NOT reproducible: committed dataset differs from generator output."
        )
        raise typer.Exit(0 if ok else 1)
    try:
        res = write_dataset(force=force)
    except FrozenDatasetError as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(1) from exc
    typer.echo(res.message)
    typer.echo(f"sha256: {res.sha256}")


@app.command("validate-dataset")
def validate_dataset_cmd(path: Path = TRANSCRIPTS_PATH) -> None:
    """Validate schema, category balance, required fields and duplicate content."""
    from voice_eval.dataset_validation import read_jsonl, validate_records

    if not path.exists():
        typer.secho(f"{rel(path)} not found — run generate-dataset first.", fg="red")
        raise typer.Exit(1)
    rep = validate_records(read_jsonl(path))
    s = rep.stats
    typer.echo(f"Transcripts: {rep.total}")
    typer.echo(f"By category: {json.dumps(s['by_category'])}")
    typer.echo(f"By difficulty: {json.dumps(s['by_difficulty'])}")
    typer.echo(f"By quality tier: {json.dumps(s['by_quality_tier'])}")
    typer.echo(f"Expected gate violations: {json.dumps(s['expected_gate_violations'])}")
    typer.echo(
        f"Modifiers: {json.dumps(s['modifiers'])}  injection classes: {json.dumps(s['prompt_injection_classes'])}"
    )
    typer.echo(f"Turns: {s['turns']}  Words: {s['words']}")
    d = s["duplicate_check"]
    typer.echo(
        f"Exact duplicate conversations: {d['exact_duplicate_conversations']}; "
        f"max pairwise 5-gram Jaccard: {d['max_pairwise_jaccard']} (mean {d['mean_pairwise_jaccard']}); "
        f"near-duplicate pairs >= {d['near_duplicate_threshold']}: {len(d['near_duplicate_pairs'])}"
    )
    for w in rep.warnings:
        typer.secho(f"WARNING: {w}", fg="yellow")
    for e in rep.errors:
        typer.secho(f"ERROR: {e}", fg="red")
    typer.secho("VALID" if rep.ok else "INVALID", fg="green" if rep.ok else "red")
    raise typer.Exit(0 if rep.ok else 1)


@app.command("list-rubrics")
def list_rubrics_cmd() -> None:
    """List available rubric versions."""
    from voice_eval.rubric_loader import available_rubrics, load_rubric

    for v in available_rubrics():
        r = load_rubric(v)
        typer.echo(
            f"{v:4} status={r.status:24} parent={r.parent_version or '-':4} hash={r.content_hash} "
            f"changes={len(r.changelog)}  {r.title}"
        )


# ----------------------------------------------------------------------------- evaluation
@app.command("evaluate")
def evaluate_cmd(
    rubric: RubricOpt = "v1",
    provider: Annotated[
        str, typer.Option(help="anthropic (live LLM) or heuristic (offline baseline, not an LLM)")
    ] = "anthropic",
    ids: Annotated[
        str | None, typer.Option(help="Comma-separated transcript ids (default: all)")
    ] = None,
    annotation_sample: Annotated[
        bool, typer.Option(help="Evaluate only the frozen 30-transcript sample")
    ] = False,
    demo: Annotated[
        bool, typer.Option(help="Write to results/demo (heuristic provider only)")
    ] = False,
    no_cache: Annotated[bool, typer.Option(help="Ignore cached LLM responses")] = False,
    threshold: Annotated[
        float | None, typer.Option(help="Override pass threshold for this run")
    ] = None,
) -> None:
    """Evaluate transcripts with the configured judge and save an experiment."""
    from voice_eval.annotation.annotation_service import sample_ids
    from voice_eval.pipeline import ConfigurationError, run_evaluation

    selected = _ids(ids)
    if annotation_sample:
        selected = sample_ids()
        if not selected:
            typer.secho(
                "No frozen annotation sample. Run create-annotation-sample first.", fg="red"
            )
            raise typer.Exit(1)

    def progress(i: int, tid: str) -> None:
        if i % 10 == 0 or provider == "anthropic":
            typer.echo(f"  [{i}] {tid}")

    try:
        m = run_evaluation(rubric, provider, selected, demo, not no_cache, threshold, progress)
    except ConfigurationError as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(1) from exc
    typer.echo(
        f"Experiment {m['experiment_id']} [{m['provenance']}]: {m['n_successful']} succeeded, "
        f"{m['n_failed']} failed -> {Path(m['artifacts']['evaluations']).parent}"
    )
    if m["n_failed"]:
        typer.secho(
            f"Failures recorded separately in {m['artifacts']['failures']} (never scored).",
            fg="yellow",
        )


# ----------------------------------------------------------------------------- annotation
@app.command("create-annotation-sample")
def create_sample_cmd(
    force: Annotated[bool, typer.Option(help="Re-draw a frozen sample (avoid!)")] = False,
) -> None:
    """Freeze the stratified 30-transcript annotation sample (and a held-out sample)."""
    from voice_eval.annotation.annotation_service import SampleAlreadyFrozen, create_sample
    from voice_eval.dataset_loader import load_transcripts

    try:
        s = create_sample(load_transcripts(), force=force)
    except SampleAlreadyFrozen as exc:
        typer.secho(str(exc), fg="yellow")
        raise typer.Exit(1) from exc
    typer.echo(
        f"Frozen {s['sample_size']} ids (seed {s['sampling_seed']}): {', '.join(s['transcript_ids'])}"
    )


@app.command("export-template")
def export_template_cmd(
    rubric: RubricOpt = "v1", path: Path = ANNOTATION_TEMPLATE_PATH, annotator: str = ""
) -> None:
    """Write a blank annotation CSV template for the frozen sample."""
    from voice_eval.annotation.annotation_service import sample_ids
    from voice_eval.annotation.import_export import export_template

    ids = sample_ids()
    if not ids:
        typer.secho("No frozen annotation sample. Run create-annotation-sample first.", fg="red")
        raise typer.Exit(1)
    export_template(ids, path, rubric, annotator)
    typer.echo(f"Template with {len(ids)} rows written to {rel(path)}")


@app.command("import-annotations")
def import_annotations_cmd(
    path: Path,
    rubric: RubricOpt = "v1",
    confirm_overwrite: Annotated[
        bool, typer.Option(help="Allow overwriting completed labels")
    ] = False,
    dry_run: Annotated[bool, typer.Option(help="Validate only")] = False,
) -> None:
    """Validate and import human annotations (CSV or JSON) into the local store."""
    from voice_eval.annotation.annotation_service import AnnotationStore, sample_ids
    from voice_eval.annotation.import_export import import_file

    rep = import_file(path, sample_ids() or None, rubric)
    typer.echo(json.dumps(rep.summary(), indent=2))
    if not rep.ok:
        typer.secho("Import has errors; nothing written.", fg="red")
        raise typer.Exit(1)
    if dry_run:
        return
    res = AnnotationStore().import_annotations(rep.annotations, confirm_overwrite)
    typer.echo(
        f"Saved {len(res['saved'])}; skipped (already completed, use --confirm-overwrite) {len(res['skipped_existing'])}"
    )


@app.command("export-annotations")
def export_annotations_cmd(
    path: Path, rubric: RubricOpt = "v1", annotator: str | None = None
) -> None:
    """Export stored annotations to CSV or JSON (by file extension)."""
    from voice_eval.annotation.annotation_service import AnnotationStore
    from voice_eval.annotation.import_export import export_csv, export_json

    anns = AnnotationStore().list(annotator, rubric)
    (export_json if path.suffix.lower() == ".json" else export_csv)(anns, path)
    typer.echo(f"Exported {len(anns)} annotations to {rel(path)}")


@app.command("annotation-status")
def annotation_status_cmd(rubric: RubricOpt = "v1", annotator: str | None = None) -> None:
    """Show annotation completion progress for the frozen sample."""
    from voice_eval.annotation.annotation_service import (
        AnnotationStore,
        load_human_labels,
        sample_ids,
    )

    annotator = annotator or load_experiment_defaults()["annotation"]["annotator_id_default"]
    st = AnnotationStore().completion(sample_ids(), annotator, rubric)
    typer.echo(
        f"Local store ({annotator}, {rubric}): {st.n_completed}/{st.total} completed, "
        f"{len(st.drafts)} drafts, {len(st.missing)} not started"
    )
    lab = load_human_labels()
    typer.echo(
        f"Frozen batch {rel(HUMAN_ANNOTATIONS_PATH)}: {len(lab.annotations)}/{lab.n_required} valid; "
        f"complete={lab.complete}"
    )


@app.command("freeze-annotations")
def freeze_annotations_cmd(rubric: RubricOpt = "v1", annotator: str | None = None) -> None:
    """Freeze the completed batch to data/human_annotations.csv (requires all 30)."""
    from voice_eval.annotation.annotation_service import (
        AnnotationStore,
        BatchIncomplete,
        sample_ids,
    )

    annotator = annotator or load_experiment_defaults()["annotation"]["annotator_id_default"]
    try:
        info = AnnotationStore().freeze_batch(sample_ids(), annotator, rubric)
    except BatchIncomplete as exc:
        typer.secho(f"Cannot freeze: {exc}", fg="red")
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(info, indent=2))


# ------------------------------------------------------------------------------- analysis
def _analyse(rubric: str, experiment: str | None):
    from voice_eval.pipeline import analyse, write_analysis

    b = analyse(rubric, experiment)
    if b.experiment is None:
        typer.secho(f"No evaluation found for rubric {rubric}. Run `evaluate` first.", fg="red")
        raise typer.Exit(1)
    paths = write_analysis(b)
    return b, paths


@app.command("agreement")
def agreement_cmd(rubric: RubricOpt = "v1", experiment: str | None = None) -> None:
    """Human-vs-judge agreement (disabled until all human labels exist)."""
    b, paths = _analyse(rubric, experiment)
    typer.echo(f"Experiment: {b.experiment.id} [{b.experiment.manifest.get('provenance')}]")
    if b.agreement is None:
        typer.secho(
            f"Human-agreement metrics PENDING: {len(b.labels.annotations)}/{b.labels.n_required} frozen "
            f"human labels available ({b.human_status}). No agreement numbers were computed.",
            fg="yellow",
        )
        return
    a = b.agreement
    bm = a.binary
    typer.echo(
        f"Pairs: {a.n_pairs}; REVIEW_REQUIRED mapping: {a.review_mapping}; threshold {a.threshold:g}"
    )
    typer.echo(
        f"Binary raw agreement {bm['raw_agreement']['value']:.3f} "
        f"[{bm['raw_agreement']['ci_low']:.3f}, {bm['raw_agreement']['ci_high']:.3f}] n={bm['n']}; "
        f"kappa {bm['kappa']['value']:.3f}; false passes {bm['false_pass_count']}; false fails {bm['false_fail_count']}"
    )
    for d, m in a.per_dimension.items():
        typer.echo(
            f"  {d:22} n={m['n']:2} exact={m['exact_agreement']['value']:.2f} "
            f"within1={m['within_one_agreement']['value']:.2f} MAE={m['mae']['value']:.2f}"
        )
    typer.echo("Wrote: " + ", ".join(paths))


@app.command("disagreements")
def disagreements_cmd(rubric: RubricOpt = "v1", experiment: str | None = None) -> None:
    """Build the disagreement register (human) and spec-conformance register."""
    b, paths = _analyse(rubric, experiment)
    typer.echo(
        f"Spec-conformance register (judge vs synthetic spec, NOT human): {len(b.spec_register)} records"
    )
    if b.agreement is None:
        typer.secho("Human disagreement register PENDING (human labels incomplete).", fg="yellow")
    else:
        typer.echo(f"Human disagreement register: {len(b.human_register)} records")
    typer.echo("Wrote: " + ", ".join(p for p in paths if "register" in p))


@app.command("thresholds")
def thresholds_cmd(rubric: RubricOpt = "v1", experiment: str | None = None) -> None:
    """Threshold sweep over the configured cutoffs (critical overrides always active)."""
    b, paths = _analyse(rubric, experiment)
    cols = [
        "cutoff",
        "n_evaluated",
        "n_pass",
        "n_fail",
        "n_review_required",
        "pass_rate",
        "critical_gate_overrides",
        "est_reviewed_calls_per_month",
        "human_agreement",
        "false_pass_count",
        "false_fail_count",
    ]
    typer.echo(f"Population: full synthetic dataset, experiment {b.experiment.id}")
    typer.echo(b.thresholds[cols].to_string(index=False))
    typer.echo("Wrote: " + ", ".join(p for p in paths if "threshold" in p or "business" in p))


@app.command("analyze-all")
def analyze_all_cmd() -> None:
    """Run analysis for every rubric that has results, then rebuild charts and reports."""
    from voice_eval.pipeline import analyse, write_analysis
    from voice_eval.reporting.report_builder import build_all
    from voice_eval.rubric_loader import available_rubrics

    for v in available_rubrics():
        b = analyse(v)
        if b.experiment:
            write_analysis(b)
            typer.echo(f"{v}: analysed {b.experiment.id}")
        else:
            typer.echo(f"{v}: no results yet")
    for p in build_all():
        typer.echo(f"Wrote {p}")


@app.command("charts")
def charts_cmd() -> None:
    """Rebuild figures (HTML) and tables from saved artifacts."""
    from voice_eval.reporting.charts import build_report_figures

    for p in build_report_figures():
        typer.echo(f"Wrote {p}")


@app.command("report")
def report_cmd() -> None:
    """Build reports/*.md from saved experiment and analysis artifacts."""
    from voice_eval.reporting.report_builder import build_all

    for p in build_all():
        typer.echo(f"Wrote {p}")


@app.command("demo")
def demo_cmd() -> None:
    """Regenerate the offline demo: heuristic baseline on all rubrics + analysis + reports."""
    from voice_eval.pipeline import run_evaluation
    from voice_eval.rubric_loader import available_rubrics

    for v in available_rubrics():
        m = run_evaluation(v, "heuristic", demo=True)
        typer.echo(f"{v}: {m['experiment_id']} ({m['n_successful']} ok, {m['n_failed']} failed)")
    analyze_all_cmd()


@app.command("dashboard")
def dashboard_cmd(port: int = 8501) -> None:
    """Launch the Streamlit dashboard (no API calls on startup)."""
    raise typer.Exit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(ROOT / "app.py"),
                "--server.port",
                str(port),
            ],
            cwd=ROOT,
        )
    )


@app.command("test")
def test_cmd() -> None:
    """Run the automated test suite (no paid API calls)."""
    raise typer.Exit(subprocess.call([sys.executable, "-m", "pytest"], cwd=ROOT))


if __name__ == "__main__":
    app()
