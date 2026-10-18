"""
Export engine for MedGuide AI Evaluation Lab.

Generates:
1. Formatted GitHub-flavored Markdown evaluation reports.
2. Machine-readable serialized JSON benchmarks.
"""

import json
from typing import Dict, Any, Optional


def export_report_to_markdown(
    report: Dict[str, Any],
    baseline_comparison: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format complete evaluation report as a GitHub-flavored Markdown document.
    """
    timestamp = report.get("timestamp", "N/A")
    total_items = report.get("total_items", 0)
    duration_ms = report.get("duration_ms", 0.0)
    accuracy = report.get("accuracy", 0.0)
    macro = report.get("macro_metrics", {})
    binary = report.get("binary_metrics", {})
    conf_matrix = report.get("confusion_matrix", {})
    per_class = report.get("per_class", {})
    results = report.get("results", [])
    citation_summary = report.get("citation_summary", {})
    provenance = report.get("provenance", {})

    lines = []
    lines.append(f"# MedGuide AI — Clinical Evaluation Lab Report")
    lines.append(f"")
    lines.append(f"**Execution Timestamp:** `{timestamp}`  ")
    lines.append(f"**Dataset Scope:** {provenance.get('benchmark_type', 'Curated Gold Regression Suite')} ({total_items} probes)  ")
    lines.append(f"**Document Corpus:** {provenance.get('source_document', 'NIDDK Guiding Principles for Diabetes Care')}  ")
    lines.append(f"**Execution Latency:** `{duration_ms} ms`  ")
    lines.append(f"")

    # 1. Executive KPI Summary
    lines.append(f"## 1. Executive Performance Summary")
    lines.append(f"")
    lines.append(f"| Metric | Value | Description |")
    lines.append(f"| :--- | :--- | :--- |")
    lines.append(f"| **Overall Accuracy** | **{accuracy * 100:.1f}%** | Multi-class overall agreement across all probes |")
    lines.append(f"| **Macro Precision** | **{macro.get('precision', 0.0) * 100:.1f}%** | Unweighted average precision across 3 classes |")
    lines.append(f"| **Macro Recall** | **{macro.get('recall', 0.0) * 100:.1f}%** | Unweighted average recall across 3 classes |")
    lines.append(f"| **Macro F1 Score** | **{macro.get('f1_score', 0.0) * 100:.1f}%** | Harmonic mean of macro precision and recall |")
    lines.append(f"| **Supported Class F1** | **{binary.get('f1_score', 0.0) * 100:.1f}%** | Binary F1 score for SUPPORTED clinical claims |")
    lines.append(f"| **Specificity** | **{binary.get('specificity', 0.0) * 100:.1f}%** | True negative rate (correctly rejecting false/unsupported claims) |")
    lines.append(f"")

    # 2. Baseline Comparison Table
    if baseline_comparison and "comparison_table" in baseline_comparison:
        lines.append(f"## 2. Baseline Comparison: Retrieval-Only vs Full Production Pipeline")
        lines.append(f"")
        lines.append(f"| System | Accuracy | Macro Prec | Macro Rec | Macro F1 | Supported F1 | Contradiction Capable | Notes |")
        lines.append(f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for row in baseline_comparison["comparison_table"]:
            lines.append(
                f"| **{row['system']}** | {row['accuracy']*100:.1f}% | {row['macro_precision']*100:.1f}% | "
                f"{row['macro_recall']*100:.1f}% | {row['macro_f1']*100:.1f}% | {row['supported_f1']*100:.1f}% | "
                f"{'Yes' if row['contradiction_capable'] else 'No'} | {row['notes']} |"
            )
        lines.append(f"")
        lines.append(f"> **Pipeline Gain:** DeBERTa NLI cross-encoder provides **+{baseline_comparison.get('accuracy_gain', 0.0)*100:.1f}%** accuracy gain and **+{baseline_comparison.get('f1_gain', 0.0)*100:.1f}%** macro F1 gain over semantic similarity alone, specifically enabling directional refutation of clinical contradictions.")
        lines.append(f"")

    # 3. Confusion Matrix
    labels = conf_matrix.get("labels", ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"])
    matrix = conf_matrix.get("matrix", [])
    if matrix:
        lines.append(f"## 3. Confusion Matrix")
        lines.append(f"")
        header = "| Ground Truth \\ Predicted | " + " | ".join(f"**{lbl}**" for lbl in labels) + " |"
        sep = "| :--- | " + " | ".join(":---:" for _ in labels) + " |"
        lines.append(header)
        lines.append(sep)
        for i, row in enumerate(matrix):
            true_lbl = labels[i]
            row_str = f"| **True {true_lbl}** | " + " | ".join(str(val) for val in row) + " |"
            lines.append(row_str)
        lines.append(f"")

    # 4. Per-Class Breakdown
    if per_class:
        lines.append(f"## 4. Per-Class Classification Breakdown")
        lines.append(f"")
        lines.append(f"| Class | Support | Precision | Recall | F1 Score |")
        lines.append(f"| :--- | :---: | :---: | :---: | :---: |")
        for cls_name, vals in per_class.items():
            lines.append(
                f"| **{cls_name}** | {vals.get('support', 0)} | "
                f"{vals.get('precision', 0.0)*100:.1f}% | {vals.get('recall', 0.0)*100:.1f}% | {vals.get('f1_score', 0.0)*100:.1f}% |"
            )
        lines.append(f"")

    # 5. Citation Page Alignment Audit
    if citation_summary:
        lines.append(f"## 5. Source PDF Citation Alignment Audit")
        lines.append(f"")
        lines.append(f"- **Total In-Domain Cited Items:** {citation_summary.get('total_cited_items', 0)}")
        lines.append(f"- **Exact Page Matches:** {citation_summary.get('matched', 0)}")
        lines.append(f"- **Adjacent Page Matches (±1 page):** {citation_summary.get('adjacent', 0)}")
        lines.append(f"- **Page Mismatches:** {citation_summary.get('mismatched', 0)}")
        lines.append(f"- **Citation Alignment Rate:** **{citation_summary.get('alignment_rate', 0.0)*100:.1f}%**")
        lines.append(f"")

    # 6. Detailed Item Breakdown
    lines.append(f"## 6. Itemized Benchmark Audit ({len(results)} Probes)")
    lines.append(f"")
    lines.append(f"| ID | Claim | Ground Truth | Predicted | Correct | Entailment | Contradiction | Citation Page | Alignment |")
    lines.append(f"| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in results:
        cited = str(r.get("citation_page")) if r.get("citation_page") is not None else "N/A"
        align = r.get("citation_alignment", "N/A")
        correct_mark = "PASS" if r.get("is_correct") else "FAIL"
        claim_short = r.get("claim", "")[:60] + "..." if len(r.get("claim", "")) > 60 else r.get("claim", "")
        lines.append(
            f"| **{r.get('id')}** | {claim_short} | `{r.get('ground_truth')}` | `{r.get('predicted')}` | "
            f"**{correct_mark}** | {r.get('entailment', 0.0):.3f} | {r.get('contradiction', 0.0):.3f} | "
            f"{cited} | `{align}` |"
        )
    lines.append(f"")

    # 7. Methodological Limitations
    lines.append(f"## 7. Methodological Limitations & Provenance")
    lines.append(f"")
    for lim in provenance.get("limitations", []):
        lines.append(f"- {lim}")
    lines.append(f"")

    return "\n".join(lines)


def export_report_to_json(
    report: Dict[str, Any],
    baseline_comparison: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format evaluation report as an indented JSON string.
    """
    export_payload = dict(report)
    if baseline_comparison:
        export_payload["baseline_comparison"] = baseline_comparison
    return json.dumps(export_payload, indent=2)
