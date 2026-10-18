import React from 'react';
import type { Source } from '../types/api';
import { FileText, ExternalLink, Database } from 'lucide-react';

interface SourceListProps {
  sources: Source[];
  onViewEvidence: (source: Source) => void;
}

export const SourceList: React.FC<SourceListProps> = ({ sources, onViewEvidence }) => {
  return (
    <div className="sources-section card glass-panel">
      <div className="card-header-row">
        <h3 className="section-title">
          <Database size={16} className="neon-teal" />
          <span>RETRIEVED GUIDELINE SOURCES</span>
        </h3>
        <span className="source-count-pill">{sources.length} Chunks</span>
      </div>

      <div className="source-meta-banner">
        <h4 className="source-book-title">NIDDK Guiding Principles for Diabetes Care</h4>
        <span className="source-org">National Diabetes Education Program • NIH / CDC</span>
      </div>

      <div className="sources-list">
        {sources.map((source) => (
          <div key={source.chunk_id} className="source-card">
            <div className="source-info">
              <FileText size={16} className="source-icon neon-emerald" />
              <div className="source-titles">
                <span className="source-page-text">Page {source.page}</span>
                <span className="source-chunk-id">{source.chunk_id}</span>
              </div>
            </div>
            <button className="view-evidence-btn" onClick={() => onViewEvidence(source)}>
              <span>Inspect Chunk</span>
              <ExternalLink size={13} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
