import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchBoxProps {
  initialQuery?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  initialQuery = '',
  onSearch,
  isLoading = false,
}) => {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <form className={`search-box glass-input-panel ${isLoading ? 'is-loading' : ''}`} onSubmit={handleSubmit}>
      <div className="search-input-prefix">
        {isLoading ? (
          <Loader2 size={20} className="icon-spin neon-cyan" />
        ) : (
          <Search size={20} className="neon-emerald" />
        )}
      </div>

      <input
        type="text"
        className="search-input"
        placeholder="Ask a medical query grounded in diabetes guidelines (e.g. Risk factors for type 2 diabetes)..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={isLoading}
        aria-label="Search clinical questions"
      />

      <button
        type="submit"
        className="search-button-neon"
        disabled={isLoading || !query.trim()}
        aria-label="Execute clinical inquiry"
      >
        <span>Execute Inquire</span>
      </button>
    </form>
  );
};
