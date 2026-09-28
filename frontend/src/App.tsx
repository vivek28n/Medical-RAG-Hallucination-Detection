import React, { useState } from 'react';
import { Search, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';

function App() {
  const [query, setQuery] = useState('');

  const suggestions = [
    "What are the risk factors for type 2 diabetes?",
    "What is prediabetes?",
    "How can diabetes be prevented or delayed?"
  ];

  const handleSuggestionClick = (text: string) => {
    setQuery(text);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Future API call will go here
      console.log('Searching for:', query);
    }
  };

  return (
    <>
      <header className="header">
        <div className="header-container">
          <div className="brand-area">
            <span className="brand-name">MedGuide</span>
            <span className="brand-desc">Medical Evidence Assistant</span>
          </div>
          <div className="nav-area">
            <nav className="nav-links">
              <a href="#">Guidelines</a>
              <a href="#">How it works</a>
              <a href="#">About</a>
            </nav>
            <div className="status-indicator">
              <div className="status-dot"></div>
              <span>System ready</span>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <h1>Evidence, before answers.</h1>
          <p>Ask questions grounded in trusted medical guidelines and research documents.</p>
        </section>

        <section className="search-section">
          <div className="search-container">
            <form className="search-box" onSubmit={handleSubmit}>
              <input
                type="text"
                className="search-input"
                placeholder="What would you like to know?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search questions"
              />
              <button type="submit" className="search-button" aria-label="Search">
                <Search size={20} />
              </button>
            </form>
          </div>

          <div className="search-suggestions">
            <span className="search-suggestions-label">Try asking</span>
            <div className="suggestions-list">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="suggestion-btn"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <div className="trust-item">
            <ShieldCheck size={28} className="trust-icon" strokeWidth={1.5} />
            <span className="trust-title">Evidence grounded</span>
            <span className="trust-desc">Responses are generated from retrieved medical documents.</span>
          </div>
          <div className="trust-item">
            <CheckCircle2 size={28} className="trust-icon" strokeWidth={1.5} />
            <span className="trust-title">Claim verification</span>
            <span className="trust-desc">Claims are checked against supporting evidence.</span>
          </div>
          <div className="trust-item">
            <FileText size={28} className="trust-icon" strokeWidth={1.5} />
            <span className="trust-title">Source citations</span>
            <span className="trust-desc">Relevant document pages remain visible.</span>
          </div>
        </section>

        <section className="empty-state">
          <FileText size={48} className="empty-icon" strokeWidth={1} />
          <h2 className="empty-title">Your evidence review will appear here</h2>
          <p className="empty-desc">Ask a question above to retrieve grounded medical information.</p>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-container">
          <div className="footer-brand">
            <strong>MedGuide</strong>
            <span>Evidence-grounded medical information</span>
          </div>
          <div className="footer-links">
            <a href="#">Prototype • Research project</a>
          </div>
          <div className="footer-disclaimer">
            Not a substitute for professional medical advice.
          </div>
        </div>
      </footer>
    </>
  );
}

export default App;
