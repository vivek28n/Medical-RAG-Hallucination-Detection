import { useState } from 'react';
import { FileText } from 'lucide-react';
import { KnowledgeBaseExplorer } from './KnowledgeBaseExplorer';

interface GuidelinesSectionProps {
  onOpenKnowledgeBase?: () => void;
}

export const GuidelinesSection: React.FC<GuidelinesSectionProps> = ({ onOpenKnowledgeBase }) => {
  const [modalOpen, setModalOpen] = useState(false);

  const handleOpen = () => {
    if (onOpenKnowledgeBase) {
      onOpenKnowledgeBase();
    } else {
      setModalOpen(true);
    }
  };

  return (
    <section id="guidelines" className="guidelines-section">
      <div className="content-container">
        <div className="section-header">
          <h2>Evidence from trusted medical documents</h2>
          <p>Answers are grounded in documents indexed by the retrieval pipeline.</p>
        </div>
        <div className="document-card">
          <div className="doc-icon"><FileText size={32} strokeWidth={1.5} /></div>
          <div className="doc-info">
            <h3>Guiding Principles for the Care of People With or at Risk for Diabetes</h3>
            <ul className="doc-meta">
              <li>Medical guideline document</li>
              <li>83 pages</li>
              <li>Indexed for retrieval</li>
              <li>FAISS-backed search</li>
            </ul>
            <button className="doc-details-btn" onClick={handleOpen}>
              View document details
            </button>
          </div>
        </div>
        {!onOpenKnowledgeBase && (
          <KnowledgeBaseExplorer isOpen={modalOpen} onClose={() => setModalOpen(false)} />
        )}
      </div>
    </section>
  );
};
