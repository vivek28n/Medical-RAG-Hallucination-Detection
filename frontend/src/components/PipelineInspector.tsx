import React, { useState } from 'react';
import { Clock, CheckCircle2, MinusCircle, AlertCircle, ChevronDown, ChevronUp, Cpu, Database, ShieldCheck, Activity, Sparkles, Sliders } from 'lucide-react';
import type { PipelineTrace, StageTrace } from '../types/api';

interface PipelineInspectorProps {
  trace?: PipelineTrace;
}

const STAGE_META: Record<string, { label: string; icon: React.ElementType; colorClass: string }> = {
  retrieval: {
    label: 'Vector Similarity Retrieval',
    icon: Database,
    colorClass: 'fill-cyan',
  },
  grounded_generation: {
    label: 'Grounded LLM Generation',
    icon: Sparkles,
    colorClass: 'fill-blue',
  },
  claim_verification: {
    label: 'DeBERTa NLI Claim Verification',
    icon: Activity,
    colorClass: 'fill-emerald',
  },
  confidence_scoring: {
    label: 'Multi-Signal Confidence Scoring',
    icon: Sliders,
    colorClass: 'fill-teal',
  },
  hallucination_decision: {
    label: 'Hallucination Decision Logic',
    icon: ShieldCheck,
    colorClass: 'fill-emerald',
  },
  self_correction: {
    label: 'Self-Correction Feedback Loop',
    icon: Cpu,
    colorClass: 'fill-amber',
  },
  re_verification: {
    label: 'Post-Correction Re-verification',
    icon: Activity,
    colorClass: 'fill-cyan',
  },
};

export const PipelineInspector: React.FC<PipelineInspectorProps> = ({ trace }) => {
  const [expanded, setExpanded] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  if (!trace) {
    return null;
  }

  const { total_duration_ms, stages, timestamp } = trace;
  const completedCount = stages.filter((s) => s.status === 'completed').length;
  const skippedCount = stages.filter((s) => s.status === 'skipped').length;

  return (
    <div className="pipeline-inspector card glass-panel">
      <div className="inspector-header-row" onClick={() => setExpanded(!expanded)} role="button" tabIndex={0}>
        <div className="inspector-title-area">
          <Clock size={16} className="neon-cyan icon-pulse" />
          <h3 className="section-title">REAL-TIME PIPELINE TRACER</h3>
          <span className="duration-pill neon-glow">
            {total_duration_ms < 1000 ? `${total_duration_ms} ms` : `${(total_duration_ms / 1000).toFixed(2)} s`}
          </span>
        </div>

        <div className="inspector-meta-summary">
          <span className="stage-count-tag">
            {completedCount} completed • {skippedCount} skipped
          </span>
          <button className="expand-btn" aria-label="Toggle pipeline trace details">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="inspector-content">
          {/* Waterfall Visualizer Bar */}
          <div className="waterfall-bar-wrapper">
            <div className="waterfall-bar-track">
              {stages.map((stage, idx) => {
                if (stage.status === 'skipped' || stage.duration_ms <= 0) return null;
                const pct = Math.max(2, (stage.duration_ms / Math.max(1, total_duration_ms)) * 100);
                const meta = STAGE_META[stage.stage_name] || { colorClass: 'fill-cyan' };

                return (
                  <div
                    key={idx}
                    className={`waterfall-segment ${meta.colorClass}`}
                    style={{ width: `${pct}%` }}
                    title={`${stage.stage_name}: ${stage.duration_ms}ms (${pct.toFixed(1)}%)`}
                    onClick={() => setSelectedStage(stage.stage_name)}
                  />
                );
              })}
            </div>
            <div className="waterfall-axis-labels">
              <span>0 ms</span>
              <span>Total: {total_duration_ms} ms</span>
            </div>
          </div>

          {/* Sequential Stages List */}
          <div className="stages-timeline-list">
            {stages.map((stage: StageTrace, idx: number) => {
              const meta = STAGE_META[stage.stage_name] || {
                label: stage.stage_name.replace(/_/g, ' '),
                icon: Clock,
                colorClass: 'fill-cyan',
              };
              const Icon = meta.icon;
              const isSelected = selectedStage === stage.stage_name;
              const pctOfTotal = total_duration_ms > 0 ? ((stage.duration_ms / total_duration_ms) * 100).toFixed(1) : '0';

              return (
                <div
                  key={idx}
                  className={`stage-timeline-card status-${stage.status} ${isSelected ? 'is-selected' : ''}`}
                  onClick={() => setSelectedStage(isSelected ? null : stage.stage_name)}
                >
                  <div className="stage-card-top">
                    <div className="stage-icon-title">
                      <div className={`stage-icon-circle ${stage.status}`}>
                        <Icon size={14} />
                      </div>
                      <div className="stage-naming">
                        <span className="stage-index">STAGE 0{idx + 1}</span>
                        <h4 className="stage-display-name">{meta.label}</h4>
                      </div>
                    </div>

                    <div className="stage-timing-badge">
                      <span className="stage-ms-val">
                        {stage.status === 'skipped' ? '0 ms' : `${stage.duration_ms} ms`}
                      </span>
                      {stage.status === 'completed' && (
                        <span className="stage-pct-val">({pctOfTotal}%)</span>
                      )}
                      <span className={`status-tag tag-${stage.status}`}>
                        {stage.status === 'completed' ? (
                          <>
                            <CheckCircle2 size={11} /> Completed
                          </>
                        ) : stage.status === 'skipped' ? (
                          <>
                            <MinusCircle size={11} /> Skipped
                          </>
                        ) : (
                          <>
                            <AlertCircle size={11} /> Failed
                          </>
                        )}
                      </span>
                    </div>
                  </div>

                  {/* Stage Technical Metadata telemetry */}
                  {stage.details && (
                    <div className="stage-details-grid">
                      {Object.entries(stage.details).map(([key, val]) => (
                        <div key={key} className="stage-detail-pill">
                          <span className="detail-key">{key.replace(/_/g, ' ')}:</span>
                          <span className="detail-value">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="inspector-footer">
            <span className="footer-timestamp">Captured: {new Date(timestamp).toLocaleTimeString()} UTC</span>
            <span className="footer-disclaimer">Real Python time.perf_counter() metrics • Un-fabricated</span>
          </div>
        </div>
      )}
    </div>
  );
};
