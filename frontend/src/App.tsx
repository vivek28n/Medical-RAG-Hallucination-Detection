import { useState, useRef, useEffect } from 'react';
import { Header } from './components/Header';
import { SearchBox } from './components/SearchBox';
import { AnswerSection } from './components/AnswerSection';
import { VerificationSummary } from './components/VerificationSummary';
import { ClaimVerification } from './components/ClaimVerification';
import { SourceList } from './components/SourceList';
import { EvidenceDrawer } from './components/EvidenceDrawer';
import { VerificationDetails } from './components/VerificationDetails';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';
import { Capabilities } from './components/Capabilities';
import { HowItWorks } from './components/HowItWorks';
import { GuidelinesSection } from './components/GuidelinesSection';
import { AboutSection } from './components/AboutSection';
import { HolographicHeart, type HeartStatus } from './components/HolographicHeart';
import { SystemTelemetry } from './components/SystemTelemetry';
import { PipelineInspector } from './components/PipelineInspector';
import { EvaluationLab } from './components/EvaluationLab';
import { KnowledgeBaseExplorer } from './components/KnowledgeBaseExplorer';
import { askMedicalQuestion, checkSystemHealth, ApiError } from './services/api';
import type { AskResponse, Source } from './types/api';
import { RotateCcw, Sparkles } from 'lucide-react';

type AppState = 'landing' | 'loading' | 'result' | 'error';

function App() {
  const [appState, setAppState] = useState<AppState>('landing');
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState('Reviewing medical evidence…');
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [isSystemReady, setIsSystemReady] = useState<boolean | null>(null);
  const [showEvaluationLab, setShowEvaluationLab] = useState(false);
  const [showKnowledgeBase, setShowKnowledgeBase] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const suggestions = [
    "What are the risk factors for type 2 diabetes?",
    "What is prediabetes?",
    "How can diabetes be prevented or delayed?"
  ];

  // Check backend health periodically
  useEffect(() => {
    let mounted = true;
    const pollHealth = async () => {
      try {
        const data = await checkSystemHealth();
        if (mounted) {
          setIsSystemReady(data.ready);
        }
      } catch {
        if (mounted) {
          setIsSystemReady(false);
        }
      }
    };

    pollHealth();
    const interval = setInterval(pollHealth, 20000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSearch = async (newQuery: string) => {
    if (!newQuery.trim()) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const newController = new AbortController();
    abortControllerRef.current = newController;

    setQuery(newQuery);
    setErrorMessage(undefined);
    setAppState('loading');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    setLoadingStep("Reviewing medical evidence…");

    try {
      const data = await askMedicalQuestion(newQuery, newController.signal);
      setResponse(data);
      setAppState('result');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("MedGuide could not complete the evidence review. Please verify backend connection.");
      }
      setAppState('error');
    } finally {
      if (abortControllerRef.current === newController) {
        abortControllerRef.current = null;
      }
    }
  };

  const handleSelectChunk = (chunkId: string) => {
    setActiveChunkId(chunkId);
    setTimeout(() => {
      const el = document.getElementById(`source-chunk-${chunkId}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  const handleJumpToClaim = (claimNumber: number) => {
    setTimeout(() => {
      const el = document.getElementById(`claim-row-${claimNumber}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  const handleInspectEvidence = (source: Source) => {
    setSelectedSource(source);
    setActiveChunkId(source.chunk_id);
  };

  const resetToLanding = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setAppState('landing');
    setQuery('');
    setResponse(null);
    setSelectedSource(null);
    setActiveChunkId(null);
    setErrorMessage(undefined);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavClick = (targetId: string) => {
    if (appState !== 'landing') {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setAppState('landing');
      setQuery('');
      setResponse(null);
      setSelectedSource(null);
      setActiveChunkId(null);
      setErrorMessage(undefined);
      setTimeout(() => {
        if (targetId === 'top') {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
        }
      }, 50);
    } else {
      if (targetId === 'top') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  // Determine heart visual status mapped to authentic pipeline states
  const heartStatus: HeartStatus =
    appState === 'loading'
      ? 'loading'
      : appState === 'error'
      ? 'error'
      : appState === 'result' && response?.hallucination_decision?.decision === 'CONTRADICTED'
      ? 'contradicted'
      : appState === 'result' &&
        (response?.hallucination_decision?.decision === 'POTENTIAL HALLUCINATION' ||
         response?.self_correction?.correction_applied)
      ? 'warning'
      : appState === 'result' && response?.hallucination_decision?.decision === 'SUPPORTED'
      ? 'verified'
      : 'idle';

  return (
    <div className="dark-healthcare-app">
      {/* Background Cybernetic ECG & Particle Grids */}
      <div className="ecg-ambient-grid" />

      <Header
        onNavClick={handleNavClick}
        onOpenEvaluationLab={() => setShowEvaluationLab(true)}
        onOpenKnowledgeBase={() => setShowKnowledgeBase(true)}
      />

      <main className="dashboard-container" id="top">
        {/* Top Inquiry Console (Search + Suggestion Chips) */}
        <section className="search-console-wrapper">
          <div className="console-headline-row">
            <div className="console-tag">
              <Sparkles size={14} className="neon-emerald" />
              <span>CLINICAL EVIDENCE INTELLIGENCE CONSOLE</span>
            </div>
            <span className="console-doc-ref">NIDDK Diabetes Guidelines • NIH Publication</span>
          </div>

          <SearchBox onSearch={handleSearch} isLoading={appState === 'loading'} initialQuery={query} />

          <div className="search-suggestions-row">
            <span className="suggestions-prefix">Clinical Inquiries:</span>
            <div className="suggestions-chips-group">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  className="suggestion-chip"
                  onClick={() => handleSearch(s)}
                  disabled={appState === 'loading'}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Dual-Column Healthcare Workspace */}
        <div className="workspace-dual-grid">
          {/* LEFT COLUMN: Clinical Review Workflow */}
          <div className="left-workflow-pane">
            {appState === 'landing' && (
              <div className="landing-content-stack">
                <Capabilities />
                <HowItWorks />
                <GuidelinesSection onOpenKnowledgeBase={() => setShowKnowledgeBase(true)} />
                <AboutSection />
              </div>
            )}

            {appState === 'loading' && (
              <div className="loading-workflow-wrapper">
                <LoadingState step={loadingStep} />
              </div>
            )}

            {appState === 'error' && (
              <div className="error-workflow-wrapper">
                <ErrorState onRetry={() => handleSearch(query)} message={errorMessage} />
              </div>
            )}

            {appState === 'result' && response && (
              <div className="result-workflow-stack">
                <div className="result-header-bar">
                  <div className="result-title-meta">
                    <span className="query-label">ACTIVE INQUIRY</span>
                    <h2 className="result-query-title">"{query}"</h2>
                  </div>
                  <button className="new-inquiry-btn" onClick={resetToLanding}>
                    <RotateCcw size={14} />
                    <span>New Inquiry</span>
                  </button>
                </div>

                <AnswerSection
                  answer={response.answer}
                  isCorrected={response.self_correction?.correction_applied}
                />

                <PipelineInspector trace={response.pipeline_trace} />

                <ClaimVerification
                  claims={response.claim_verification?.claims || []}
                  activeChunkId={activeChunkId}
                  onSelectChunk={handleSelectChunk}
                  onInspectEvidence={handleInspectEvidence}
                />

                <SourceList
                  sources={response.sources || []}
                  claims={response.claim_verification?.claims || []}
                  activeChunkId={activeChunkId}
                  onViewEvidence={handleInspectEvidence}
                  onJumpToClaim={handleJumpToClaim}
                />
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: 3D Holographic Heart Core & Real-time Telemetry */}
          <div className="right-telemetry-pane">
            {/* Holographic 3D Viewport Card */}
            <div className="holographic-core-card glass-panel">
              <div className="core-header">
                <div className="core-title">
                  <span className="radar-blip"></span>
                  <span>HOLOGRAPHIC 3D CARDIAC CORE</span>
                </div>
                <span className="core-subtext">Interactive WebGL Wireframe</span>
              </div>

              <HolographicHeart
                status={heartStatus}
                latencyMs={response?.pipeline_trace?.total_duration_ms}
                confidenceLevel={response?.confidence?.confidence_level}
                isCorrected={response?.self_correction?.correction_applied}
              />
            </div>

            {/* When viewing results: Display Verification HUD & Confidence Signals */}
            {appState === 'result' && response?.hallucination_decision && response?.confidence && response?.claim_verification && (
              <>
                <VerificationSummary
                  decision={response.hallucination_decision}
                  confidence={response.confidence}
                  verification={response.claim_verification}
                />

                <VerificationDetails confidence={response.confidence} />
              </>
            )}

            {/* Subsystem Technical Health Card */}
            <SystemTelemetry isReady={isSystemReady} totalVectors={268} />
          </div>
        </div>
      </main>

      <footer className="footer-dark">
        <div className="footer-container">
          <div className="footer-brand">
            <strong>MedGuide Clinical RAG</strong>
            <span>Evidence Grounding &amp; Hallucination Detection</span>
          </div>
          <div className="footer-links">
            <a href="#guidelines" onClick={(e) => { e.preventDefault(); handleNavClick('guidelines'); }}>Guidelines</a>
            <a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleNavClick('how-it-works'); }}>How it works</a>
            <a href="#about" onClick={(e) => { e.preventDefault(); handleNavClick('about'); }}>About</a>
            <a href="#knowledge-base" onClick={(e) => { e.preventDefault(); setShowKnowledgeBase(true); }}>Knowledge Base</a>
            <a href="#evaluation" onClick={(e) => { e.preventDefault(); setShowEvaluationLab(true); }}>Evaluation Lab</a>
          </div>
          <div className="footer-meta-links">
            <span className="footer-disclaimer">For clinical research &amp; educational verification. Not medical advice.</span>
            <span className="footer-project-type">FAISS • DeBERTa-v3 • Gemini 3 Flash Preview</span>
          </div>
        </div>
      </footer>

      <EvidenceDrawer
        source={selectedSource}
        claims={response?.claim_verification?.claims || []}
        onClose={() => setSelectedSource(null)}
        onJumpToClaim={handleJumpToClaim}
      />

      <EvaluationLab
        isOpen={showEvaluationLab}
        onClose={() => setShowEvaluationLab(false)}
      />

      <KnowledgeBaseExplorer
        isOpen={showKnowledgeBase}
        onClose={() => setShowKnowledgeBase(false)}
      />
    </div>
  );
}

export default App;
