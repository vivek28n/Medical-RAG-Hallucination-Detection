import React from 'react';
import { CheckCircle2, AlertTriangle, XOctagon } from 'lucide-react';
import type { HallucinationDecision } from '../types/api';

interface StatusBadgeProps {
  decision: HallucinationDecision['decision'];
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ decision }) => {
  if (decision === 'SUPPORTED') {
    return (
      <div className="status-badge supported-neon">
        <CheckCircle2 size={16} className="neon-emerald" />
        <span>Fully Supported by Guideline Evidence</span>
      </div>
    );
  }

  if (decision === 'POTENTIAL HALLUCINATION') {
    return (
      <div className="status-badge potential-neon">
        <AlertTriangle size={16} className="neon-amber" />
        <span>Potential Hallucination: Partial Support Detected</span>
      </div>
    );
  }

  return (
    <div className="status-badge contradicted-neon">
      <XOctagon size={16} className="neon-alert" />
      <span>Contradicted: Evidence Conflicts with Claims</span>
    </div>
  );
};
