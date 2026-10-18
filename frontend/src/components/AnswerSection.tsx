import React from 'react';
import { Sparkles, CheckCheck } from 'lucide-react';

interface AnswerSectionProps {
  answer: string;
  isCorrected?: boolean;
}

export const AnswerSection: React.FC<AnswerSectionProps> = ({ answer, isCorrected }) => {
  return (
    <div className="answer-section card glass-panel">
      <div className="card-header-row">
        <h3 className="section-title">
          <Sparkles size={16} className="neon-cyan" />
          <span>EVIDENCE-GROUNDED ANSWER</span>
        </h3>
        {isCorrected && (
          <div className="self-correction-badge">
            <CheckCheck size={14} className="neon-emerald" />
            <span>Self-Corrected via NLI Loop</span>
          </div>
        )}
      </div>

      <div className="answer-content-area">
        <p className="answer-text">{answer}</p>
      </div>

      <div className="answer-footer-meta">
        <span className="guideline-ref-tag">Source: NIDDK Guiding Principles for Diabetes Care</span>
      </div>
    </div>
  );
};
