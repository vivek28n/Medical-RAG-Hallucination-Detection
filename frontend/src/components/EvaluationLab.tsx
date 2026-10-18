import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  X,
  FileText,
  Filter,
  Check,
  Download,
  FileCode,
} from 'lucide-react';
import type { EvaluationReport, BenchmarkItem, BenchmarkProvenance } from '../types/api';
import {
  fetchBenchmark,
  runEvaluationBenchmark,
  exportEvaluationMarkdown,
  exportEvaluationJson,
} from '../services/api';

interface EvaluationLabProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EvaluationLab: React.FC<EvaluationLabProps> = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [exportingMd, setExportingMd] = useState(false);
  const [exportingJson, setExportingJson] = useState(false);
  const [benchmarkItems, setBenchmarkItems] = useState<BenchmarkItem[]>([]);
  const [provenance, setProvenance] = useState<BenchmarkProvenance | null>(null);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'CORRECT' | 'ERROR' | 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED'>('ALL');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    const loadBenchmark = async () => {
      setLoading(true);
      setErrorMsg(null);
      try {
        const data = await fetchBenchmark();
        if (mounted) {
          setBenchmarkItems(data.items);
          setProvenance(data.provenance);
        }
      } catch (err) {
        if (mounted) {
          setErrorMsg(err instanceof Error ? err.message : 'Failed to load benchmark specification.');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadBenchmark();
    return () => {
      mounted = false;
    };
  }, [isOpen]);

  const handleRunEvaluation = async () => {
    setRunning(true);
    setErrorMsg(null);
    try {
      const data = await runEvaluationBenchmark();
      setReport(data);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Evaluation run failed.');
    } finally {
      setRunning(false);
    }
  };

  const triggerDownload = (filename: string, content: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = async () => {
    setExportingMd(true);
    setErrorMsg(null);
    try {
      const res = await exportEvaluationMarkdown();
      triggerDownload(res.filename, res.content, 'text/markdown;charset=utf-8');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Markdown export failed.');
    } finally {
      setExportingMd(false);
    }
  };

  const handleExportJson = async () => {
    setExportingJson(true);
    setErrorMsg(null);
    try {
      const res = await exportEvaluationJson();
      triggerDownload(res.filename, res.content, 'application/json;charset=utf-8');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'JSON export failed.');
    } finally {
      setExportingJson(false);
    }
  };

  if (!isOpen) return null;

  // Filter items
  const displayResults = report?.results.filter((item) => {
    if (filter === 'CORRECT') return item.is_correct;
    if (filter === 'ERROR') return !item.is_correct;
    if (filter === 'SUPPORTED') return item.ground_truth === 'SUPPORTED';
    if (filter === 'CONTRADICTED') return item.ground_truth === 'CONTRADICTED';
    if (filter === 'UNSUPPORTED') return item.ground_truth === 'UNSUPPORTED';
    return true;
  }) || [];

  return (
    <div className="evaluation-lab-modal-overlay" role="presentation">
      <div className="evaluation-lab-container card glass-panel" role="dialog" aria-modal="true" aria-labelledby="eval-lab-title">
        {/* Header */}
        <div className="eval-lab-header">
          <div className="eval-title-group">
            <div className="eval-title-row">
              <FlaskConical size={20} className="neon-cyan" />
              <h2 id="eval-lab-title" className="eval-heading">CLINICAL EVALUATION LAB</h2>
              <span className="eval-version-pill">Benchmark v2.0 (Phase 2)</span>
            </div>
            <p className="eval-subtext">
              Curated Gold Regression Suite • NIDDK Guiding Principles for Diabetes Care
            </p>
          </div>

          <div className="eval-actions-group">
            {report && (
              <>
                <button
                  className="eval-export-btn"
                  onClick={handleExportMarkdown}
                  disabled={exportingMd || running}
                  title="Export GitHub-Flavored Markdown Report"
                >
                  <Download size={13} />
                  <span>{exportingMd ? 'Exporting…' : 'Export .MD'}</span>
                </button>
                <button
                  className="eval-export-btn"
                  onClick={handleExportJson}
                  disabled={exportingJson || running}
                  title="Export Raw Serialized JSON Report"
                >
                  <FileCode size={13} />
                  <span>{exportingJson ? 'Exporting…' : 'Export .JSON'}</span>
                </button>
              </>
            )}
            <button
              className="run-eval-btn"
              onClick={handleRunEvaluation}
              disabled={running || loading}
            >
              {running ? (
                <>
                  <RotateCcw size={14} className="icon-spin" />
                  <span>Evaluating 15 Probes…</span>
                </>
              ) : (
                <>
                  <Play size={14} />
                  <span>{report ? 'Re-Run Evaluation' : 'Run Benchmark Evaluation'}</span>
                </>
              )}
            </button>
            <button className="close-eval-btn" onClick={onClose} aria-label="Close Evaluation Lab">
              <X size={18} />
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="eval-error-banner">
            <ShieldAlert size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="eval-scroll-content">
          {/* KPI Summary Cards */}
          {report ? (
            <div className="eval-metrics-kpi-grid">
              <div className="kpi-card highlight-cyan">
                <span className="kpi-label">OVERALL ACCURACY</span>
                <span className="kpi-value text-cyan">{(report.accuracy * 100).toFixed(1)}%</span>
                <span className="kpi-meta">
                  {report.results.filter((r) => r.is_correct).length} / {report.total_items} correct
                </span>
              </div>

              <div className="kpi-card highlight-emerald">
                <span className="kpi-label">MACRO PRECISION</span>
                <span className="kpi-value text-emerald">{(report.macro_metrics.precision * 100).toFixed(1)}%</span>
                <span className="kpi-meta">Unweighted across 3 classes</span>
              </div>

              <div className="kpi-card highlight-teal">
                <span className="kpi-label">MACRO RECALL</span>
                <span className="kpi-value text-teal">{(report.macro_metrics.recall * 100).toFixed(1)}%</span>
                <span className="kpi-meta">Sensitivity across all classes</span>
              </div>

              <div className="kpi-card highlight-amber">
                <span className="kpi-label">MACRO F1-SCORE</span>
                <span className="kpi-value text-amber">{(report.macro_metrics.f1_score * 100).toFixed(1)}%</span>
                <span className="kpi-meta">Harmonic mean precision &amp; recall</span>
              </div>
            </div>
          ) : (
            <div className="eval-initial-prompt card">
              <div className="initial-prompt-inner">
                <Info size={24} className="neon-teal" />
                <div className="initial-prompt-text">
                  <h4>Curated Gold Regression Suite Ready</h4>
                  <p>
                    {benchmarkItems.length} curated clinical probes from the NIDDK guidelines (Principles 1–7) are loaded.
                    Evaluations execute generic claim-to-hypothesis generation, vector retrieval, and DeBERTa-v3 NLI classification using shared production logic.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Citation Alignment Audit Card */}
          {report?.citation_summary && (
            <div className="citation-audit-card card">
              <div className="section-title-row">
                <h3 className="section-title">CITATION AUDIT &amp; PAGE ALIGNMENT</h3>
                <span className="citation-rate-pill">
                  Audit Alignment Rate: {(report.citation_summary.alignment_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="citation-stats-row">
                <div className="citation-stat-chip">
                  <span className="chip-label">Cited Probes:</span>
                  <span className="chip-val">{report.citation_summary.total_cited_items}</span>
                </div>
                <div className="citation-stat-chip text-emerald">
                  <span className="chip-label">Exact Page Matches:</span>
                  <span className="chip-val">{report.citation_summary.matched}</span>
                </div>
                <div className="citation-stat-chip text-cyan">
                  <span className="chip-label">Adjacent Pages (±1):</span>
                  <span className="chip-val">{report.citation_summary.adjacent}</span>
                </div>
                <div className="citation-stat-chip text-amber">
                  <span className="chip-label">Page Mismatches:</span>
                  <span className="chip-val">{report.citation_summary.mismatched}</span>
                </div>
              </div>
            </div>
          )}

          {/* Baseline Comparison: Retrieval-Only vs Full Pipeline */}
          {report?.baseline_comparison && (
            <div className="baseline-comparison-section card">
              <div className="section-title-row">
                <div className="baseline-title-group">
                  <h3 className="section-title">BASELINE COMPARISON (RETRIEVAL-ONLY VS FULL PIPELINE)</h3>
                  <span className="baseline-badge">Vector Similarity Baseline vs Cross-Encoder DeBERTa-v3 NLI</span>
                </div>
                <div className="baseline-delta-chips">
                  <span className="delta-chip highlight-emerald">
                    Accuracy Gain: +{(report.baseline_comparison.accuracy_gain * 100).toFixed(1)}%
                  </span>
                  <span className="delta-chip highlight-teal">
                    Macro F1 Gain: +{(report.baseline_comparison.f1_gain * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="baseline-table-wrapper">
                <table className="baseline-table">
                  <thead>
                    <tr>
                      <th>Pipeline</th>
                      <th>Accuracy</th>
                      <th>Macro Precision</th>
                      <th>Macro Recall</th>
                      <th>Macro F1</th>
                      <th>Negation / Contradiction</th>
                      <th>Clinical Methodology</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.baseline_comparison.comparison_table.map((row) => (
                      <tr key={row.system} className={row.system.includes('MedGuide') ? 'row-highlight' : ''}>
                        <td className="system-name-cell">
                          <strong>{row.system}</strong>
                        </td>
                        <td>{(row.accuracy * 100).toFixed(1)}%</td>
                        <td>{(row.macro_precision * 100).toFixed(1)}%</td>
                        <td>{(row.macro_recall * 100).toFixed(1)}%</td>
                        <td>{(row.macro_f1 * 100).toFixed(1)}%</td>
                        <td>
                          {row.contradiction_capable ? (
                            <span className="badge-supported">Supported (NLI)</span>
                          ) : (
                            <span className="badge-unsupported">Blind to Negation</span>
                          )}
                        </td>
                        <td className="notes-cell">{row.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Interactive Confusion Matrix */}
          {report && (
            <div className="confusion-matrix-section card">
              <div className="section-title-row">
                <h3 className="section-title">CONFUSION MATRIX (GROUND TRUTH VS PREDICTED)</h3>
                <span className="matrix-badge">3×3 Multi-Class Matrix</span>
              </div>

              <div className="matrix-table-wrapper">
                <table className="confusion-matrix-table">
                  <thead>
                    <tr>
                      <th className="corner-cell">True \ Pred</th>
                      {report.confusion_matrix.labels.map((lbl) => (
                        <th key={lbl} className="col-header-cell">
                          Pred: {lbl}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.confusion_matrix.labels.map((trueLbl, rowIdx) => (
                      <tr key={trueLbl}>
                        <th className="row-header-cell">True: {trueLbl}</th>
                        {report.confusion_matrix.matrix[rowIdx].map((cnt, colIdx) => {
                          const isDiagonal = rowIdx === colIdx;
                          const cellClass = isDiagonal
                            ? cnt > 0
                              ? 'cell-match'
                              : 'cell-zero'
                            : cnt > 0
                            ? 'cell-mismatch'
                            : 'cell-zero';
                          return (
                            <td key={colIdx} className={`matrix-count-cell ${cellClass}`}>
                              <span className="cell-count-num">{cnt}</span>
                              {cnt > 0 && isDiagonal && <Check size={12} className="cell-check-icon" />}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="binary-diagnostic-row">
                <span className="diagnostic-chip">
                  Specificity: {(report.binary_metrics.specificity! * 100).toFixed(1)}%
                </span>
                <span className="diagnostic-chip">
                  Binary Supported F1: {(report.binary_metrics.f1_score * 100).toFixed(1)}%
                </span>
                <span className="diagnostic-chip">
                  Execution Latency: {report.duration_ms} ms
                </span>
              </div>
            </div>
          )}

          {/* Provenance & Limitations Documentation */}
          <div className="provenance-limitations-section card">
            <div className="section-title-row">
              <h3 className="section-title">BENCHMARK PROVENANCE &amp; METHODOLOGICAL LIMITATIONS</h3>
            </div>

            <div className="provenance-grid">
              <div className="provenance-col">
                <h4 className="provenance-col-title">Dataset Provenance</h4>
                <ul className="provenance-list">
                  <li>
                    <strong>Document:</strong> {provenance?.source_document || 'NIDDK Guiding Principles for Diabetes Care'}
                  </li>
                  <li>
                    <strong>Publisher:</strong> {provenance?.publisher || 'National Diabetes Education Program • NIH / CDC'}
                  </li>
                  <li>
                    <strong>Corpus Extent:</strong> 83 guideline pages • 268-chunk FAISS index
                  </li>
                  <li>
                    <strong>Verifier:</strong> Cross-encoder DeBERTa-v3-base NLI + all-MiniLM-L6-v2 embeddings
                  </li>
                  <li>
                    <strong>Scope:</strong> Curated Gold Regression Suite (15 items) • Verified against PDF text
                  </li>
                </ul>
              </div>

              <div className="provenance-col">
                <h4 className="provenance-col-title">Clinical &amp; System Limitations</h4>
                <ul className="limitations-list">
                  <li>
                    NLI premise-hypothesis entailment evaluates factual consistency against retrieved guideline text;
                    it does not replace independent peer-reviewed physician judgment.
                  </li>
                  <li>
                    An UNSUPPORTED verdict strictly denotes insufficient evidence in the indexed document,
                    not necessarily medical invalidity across wider clinical literature.
                  </li>
                  <li>
                    Evaluations are executed purely against retrieval and NLI modules without LLM calls,
                    ensuring reproducibility and zero quota consumption.
                  </li>
                  <li>
                    This 15-item suite functions as a regression safety net, not an independent validation set.
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Item-by-Item Breakdown Table */}
          <div className="benchmark-items-section card">
            <div className="section-title-row">
              <h3 className="section-title">BENCHMARK ITEM AUDIT ({displayResults.length > 0 ? displayResults.length : benchmarkItems.length})</h3>

              <div className="filter-button-group">
                <Filter size={12} className="filter-icon" />
                <button
                  className={`filter-btn ${filter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setFilter('ALL')}
                >
                  All ({report ? report.results.length : benchmarkItems.length})
                </button>
                {report && (
                  <>
                    <button
                      className={`filter-btn ${filter === 'CORRECT' ? 'active' : ''}`}
                      onClick={() => setFilter('CORRECT')}
                    >
                      Correct ({report.results.filter((r) => r.is_correct).length})
                    </button>
                    <button
                      className={`filter-btn ${filter === 'ERROR' ? 'active' : ''}`}
                      onClick={() => setFilter('ERROR')}
                    >
                      Errors ({report.results.filter((r) => !r.is_correct).length})
                    </button>
                  </>
                )}
                <button
                  className={`filter-btn ${filter === 'SUPPORTED' ? 'active' : ''}`}
                  onClick={() => setFilter('SUPPORTED')}
                >
                  Supported
                </button>
                <button
                  className={`filter-btn ${filter === 'CONTRADICTED' ? 'active' : ''}`}
                  onClick={() => setFilter('CONTRADICTED')}
                >
                  Contradicted
                </button>
                <button
                  className={`filter-btn ${filter === 'UNSUPPORTED' ? 'active' : ''}`}
                  onClick={() => setFilter('UNSUPPORTED')}
                >
                  Unsupported
                </button>
              </div>
            </div>

            <div className="benchmark-items-list">
              {report
                ? displayResults.map((item) => (
                    <div
                      key={item.id}
                      className={`benchmark-item-card ${item.is_correct ? 'is-correct-card' : 'is-mismatch-card'}`}
                    >
                      <div className="bm-card-header">
                        <div className="bm-id-row">
                          <span className="bm-id-badge">{item.id}</span>
                          <span className="bm-label-tag ground-truth">Truth: {item.ground_truth}</span>
                          <span className={`bm-label-tag predicted ${item.is_correct ? 'pred-match' : 'pred-mismatch'}`}>
                            Pred: {item.predicted}
                          </span>
                        </div>

                        <div className="bm-status-indicator">
                          {item.is_correct ? (
                            <span className="match-status correct">
                              <CheckCircle2 size={13} /> Accurate Match
                            </span>
                          ) : (
                            <span className="match-status mismatch">
                              <AlertTriangle size={13} /> Classification Mismatch
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="bm-claim-text">{item.claim}</p>

                      <div className="bm-telemetry-row">
                        <div className="bm-telemetry-cell">
                          <span className="bm-telemetry-label">NLI Entailment:</span>
                          <span className="bm-telemetry-val text-emerald">{(item.entailment * 100).toFixed(1)}%</span>
                        </div>
                        <div className="bm-telemetry-cell">
                          <span className="bm-telemetry-label">Contradiction:</span>
                          <span className="bm-telemetry-val text-slate">{(item.contradiction * 100).toFixed(1)}%</span>
                        </div>
                        <div className="bm-telemetry-cell">
                          <span className="bm-telemetry-label">Cosine Sim:</span>
                          <span className="bm-telemetry-val text-cyan">{(item.similarity * 100).toFixed(1)}%</span>
                        </div>
                        {item.citation_page && (
                          <div className="bm-telemetry-cell">
                            <span className="bm-telemetry-label">PDF Page:</span>
                            <span className="bm-telemetry-val text-primary">
                              <FileText size={11} className="inline-icon" /> Page {item.citation_page}
                              {item.booklet_page && <span className="booklet-note">(Booklet p. {item.booklet_page})</span>}
                            </span>
                          </div>
                        )}
                        {item.citation_alignment && item.citation_alignment !== 'NOT_APPLICABLE' && (
                          <div className="bm-telemetry-cell">
                            <span className="bm-telemetry-label">Citation:</span>
                            <span className={`alignment-tag align-${item.citation_alignment.toLowerCase()}`}>
                              {item.citation_alignment}
                              {item.matched_page ? ` (p. ${item.matched_page})` : ''}
                            </span>
                          </div>
                        )}
                        {item.verification_status === 'FLAGGED_FOR_HUMAN_REVIEW' && (
                          <div className="bm-telemetry-cell">
                            <span className="review-flag-badge">
                              <AlertTriangle size={11} /> Review Flag
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                : benchmarkItems.map((item) => (
                    <div key={item.id} className="benchmark-item-card unrun">
                      <div className="bm-card-header">
                        <div className="bm-id-row">
                          <span className="bm-id-badge">{item.id}</span>
                          <span className="bm-label-tag ground-truth">Truth: {item.ground_truth}</span>
                          {item.citation_page && (
                            <span className="bm-page-tag">
                              <FileText size={11} className="inline-icon" /> Page {item.citation_page}
                              {item.booklet_page && <span className="booklet-note">(Booklet p. {item.booklet_page})</span>}
                            </span>
                          )}
                          {item.verification_status === 'FLAGGED_FOR_HUMAN_REVIEW' && (
                            <span className="review-flag-badge">
                              <AlertTriangle size={11} /> Review Flag
                            </span>
                          )}
                        </div>
                        {item.principle && <span className="bm-principle-tag">{item.principle}</span>}
                      </div>

                      <p className="bm-claim-text">{item.claim}</p>
                      {item.rationale && <p className="bm-rationale-text">Rationale: {item.rationale}</p>}
                    </div>
                  ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
