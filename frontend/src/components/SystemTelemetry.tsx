import { ShieldCheck, Cpu, Database, Network, BookOpen, Activity } from 'lucide-react';

interface SystemTelemetryProps {
  isReady?: boolean | null;
  totalVectors?: number;
  activeModel?: string;
}

export const SystemTelemetry = ({
  isReady = null,
  totalVectors = 268,
  activeModel = 'Gemini 3 Flash Preview',
}: SystemTelemetryProps) => {
  return (
    <div className="telemetry-panel">
      <div className="telemetry-header">
        <div className="telemetry-title">
          <Activity className="icon-pulse neon-emerald" size={18} />
          <span>CLINICAL EVIDENCE TELEMETRY</span>
        </div>
        {isReady !== null && (
          <span className={`status-pill ${isReady ? 'ready' : 'degraded'}`}>
            <span className="status-dot"></span>
            {isReady ? 'BACKEND VERIFIED' : 'BACKEND DEGRADED'}
          </span>
        )}
      </div>

      <div className="telemetry-grid">
        <div className="telemetry-card">
          <div className="card-icon-title">
            <Database size={16} className="neon-teal" />
            <span className="card-label">VECTOR DATABASE</span>
          </div>
          <div className="card-metric">{totalVectors} Chunks</div>
          <div className="card-subtext">FAISS IndexFlatL2 • 384 dims</div>
        </div>

        <div className="telemetry-card">
          <div className="card-icon-title">
            <Cpu size={16} className="neon-cyan" />
            <span className="card-label">NLI CROSS-ENCODER</span>
          </div>
          <div className="card-metric">DeBERTa-v3</div>
          <div className="card-subtext">3-Label Entailment Verifier</div>
        </div>

        <div className="telemetry-card">
          <div className="card-icon-title">
            <Network size={16} className="neon-emerald" />
            <span className="card-label">GENERATIVE LLM</span>
          </div>
          <div className="card-metric truncate">{activeModel}</div>
          <div className="card-subtext">Multi-Tier Auto Fallback</div>
        </div>

        <div className="telemetry-card">
          <div className="card-icon-title">
            <BookOpen size={16} className="neon-teal" />
            <span className="card-label">KNOWLEDGE BASE</span>
          </div>
          <div className="card-metric">NIDDK Diabetes</div>
          <div className="card-subtext">83 Guideline Pages Indexed</div>
        </div>
      </div>

      <div className="telemetry-footer">
        <div className="telemetry-footnote">
          <ShieldCheck size={14} className="neon-emerald" />
          <span>Self-Correction loop active on confidence &lt; 0.60 or contradiction</span>
        </div>
      </div>
    </div>
  );
};
