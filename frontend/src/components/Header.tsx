import React from 'react';
import { Activity, FlaskConical, Database } from 'lucide-react';

interface HeaderProps {
  onNavClick: (targetId: string) => void;
  onOpenEvaluationLab?: () => void;
  onOpenKnowledgeBase?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onNavClick,
  onOpenEvaluationLab,
  onOpenKnowledgeBase,
}) => {
  const handleClick = (e: React.MouseEvent<HTMLElement>, id: string) => {
    e.preventDefault();
    onNavClick(id);
  };

  return (
    <header className="header">
      <div className="header-container">
        <div
          className="brand-area"
          style={{ cursor: 'pointer' }}
          onClick={(e) => handleClick(e, 'top')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && handleClick(e as unknown as React.MouseEvent<HTMLElement>, 'top')}
        >
          <div className="brand-logo-icon">
            <Activity className="neon-emerald icon-pulse" size={22} />
          </div>
          <div className="brand-titles">
            <div className="brand-name-row">
              <span className="brand-name">MedGuide</span>
              <span className="brand-tag">RAG v1.0</span>
            </div>
            <span className="brand-desc">Medical Evidence &amp; Hallucination Detection</span>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#guidelines" onClick={(e) => handleClick(e, 'guidelines')}>Guidelines</a>
          <a href="#how-it-works" onClick={(e) => handleClick(e, 'how-it-works')}>How it works</a>
          <a href="#about" onClick={(e) => handleClick(e, 'about')}>About</a>
          <a
            href="#knowledge-base"
            className="nav-kb-link"
            onClick={(e) => {
              e.preventDefault();
              onOpenKnowledgeBase?.();
            }}
          >
            <Database size={13} className="inline-icon neon-teal" />
            <span>Knowledge Base</span>
          </a>
          <a
            href="#evaluation"
            className="nav-eval-link"
            onClick={(e) => {
              e.preventDefault();
              onOpenEvaluationLab?.();
            }}
          >
            <FlaskConical size={13} className="inline-icon neon-cyan" />
            <span>Evaluation Lab</span>
          </a>
        </nav>
      </div>
    </header>
  );
};
