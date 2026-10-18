import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Database, Cpu, Sparkles } from 'lucide-react';

interface LoadingStateProps {
  step?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ step }) => {
  const steps = [
    { label: 'Vector Similarity Retrieval', desc: 'Querying 268 guideline chunks in FAISS FlatL2', icon: Database },
    { label: 'Context Assembly & Grounded Prompting', desc: 'Filtering citation noise from diabetes guidelines', icon: Sparkles },
    { label: 'LLM Generation & Fallback Check', desc: 'Synthesizing evidence-bound clinical statements', icon: Cpu },
    { label: 'DeBERTa NLI Claim Verification', desc: 'Cross-encoding premise-hypothesis pairs', icon: Activity },
    { label: 'Multi-Signal Confidence Scoring', desc: 'Evaluating semantic similarity & claim consistency', icon: ShieldCheck },
  ];

  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStepIdx((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 2400);
    return () => clearInterval(timer);
  }, [steps.length]);

  return (
    <div className="loading-state glass-panel">
      <div className="loading-radar-animation">
        <div className="radar-circle ring-1"></div>
        <div className="radar-circle ring-2"></div>
        <div className="radar-circle ring-3"></div>
        <Activity size={32} className="radar-core-icon neon-emerald" />
      </div>

      <div className="loading-header-text">
        <h3 className="loading-headline">Processing Clinical Evidence</h3>
        <p className="loading-subline">{step || steps[currentStepIdx].label}</p>
      </div>

      <div className="loading-steps-timeline">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          const isDone = idx < currentStepIdx;
          const isCurrent = idx === currentStepIdx;

          return (
            <div
              key={idx}
              className={`timeline-step-row ${isDone ? 'done' : ''} ${isCurrent ? 'active' : ''}`}
            >
              <div className="timeline-node">
                <Icon size={14} />
              </div>
              <div className="timeline-text">
                <span className="step-name">{s.label}</span>
                <span className="step-desc">{s.desc}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
