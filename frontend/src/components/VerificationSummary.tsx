import React from 'react';
import { StatusBadge } from './StatusBadge';
import { Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { HallucinationDecision, Confidence, ClaimVerification } from '../types/api';

interface VerificationSummaryProps {
  decision: HallucinationDecision;
  confidence: Confidence;
  verification: ClaimVerification;
}

export const VerificationSummary: React.FC<VerificationSummaryProps> = ({
  decision,
  confidence,
  verification,
}) => {
  const isSupported = decision.decision === 'SUPPORTED';
  const confidencePercent = Math.round(confidence.confidence_score * 100);

  return (
    <div className="verification-summary card glass-panel">
      <div className="card-header-row">
        <h3 className="section-title">
          <Shield size={16} className="neon-emerald" />
          <span>VERIFICATION AUDIT</span>
        </h3>
        <span className={`decision-chip ${decision.decision.toLowerCase().replace(/\s+/g, '-')}`}>
          {decision.decision}
        </span>
      </div>

      <StatusBadge decision={decision.decision} />

      <div className="confidence-hud-display">
        <div className="confidence-hud-circle">
          <svg viewBox="0 0 100 100" className="confidence-svg-ring">
            <circle cx="50" cy="50" r="42" className="ring-track" />
            <circle
              cx="50"
              cy="50"
              r="42"
              className={`ring-fill ${confidence.confidence_level.toLowerCase()}`}
              strokeDasharray={264}
              strokeDashoffset={264 - (264 * confidence.confidence_score)}
            />
          </svg>
          <div className="hud-center-metric">
            <span className="hud-number">{confidencePercent}%</span>
            <span className="hud-label">CONFIDENCE</span>
          </div>
        </div>

        <div className="confidence-quick-stats">
          <div className="quick-stat-item">
            <span className="stat-label">Rating</span>
            <span className={`stat-value tier-${confidence.confidence_level.toLowerCase()}`}>
              {confidence.confidence_level}
            </span>
          </div>
          <div className="quick-stat-item">
            <span className="stat-label">Supported Claims</span>
            <span className="stat-value text-emerald">
              <CheckCircle2 size={13} className="inline-icon" />
              {verification.supported_claims}/{verification.total_claims}
            </span>
          </div>
          <div className="quick-stat-item">
            <span className="stat-label">Contradictions</span>
            <span className={`stat-value ${decision.strong_contradictions > 0 ? 'text-alert' : 'text-slate'}`}>
              <AlertTriangle size={13} className="inline-icon" />
              {decision.strong_contradictions}
            </span>
          </div>
        </div>
      </div>

      <p className="verification-desc">
        {isSupported
          ? "High grounding detected: retrieved clinical guideline chunks directly entail the extracted claims."
          : decision.decision === 'CONTRADICTED'
          ? "Medical caution: one or more generated statements conflict with the retrieved guideline evidence."
          : "Evidence review identified claims without strong entailment in the primary guideline document."}
      </p>
    </div>
  );
};
