import { useState } from 'react';
import { api } from '../api.js';

export default function AskBox({ farmId }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const result = await api.ask(farmId, question);
      setAnswer(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ask-box">
      <form className="ask-form" onSubmit={handleAsk}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Should I irrigate tomorrow?"
          aria-label="Ask AgriPulse a question about this farm"
        />
        <button className="btn-primary btn-small" type="submit" disabled={loading}>
          {loading ? 'Asking…' : 'Ask'}
        </button>
      </form>

      {error && <div className="status-text error">Error: {error}</div>}

      {answer && (
        <div className="ask-answer">
          <p className="rec-explanation">{answer.answer}</p>
          <button className="evidence-toggle" onClick={() => setShowEvidence(!showEvidence)}>
            {showEvidence ? 'Hide evidence used' : 'View evidence used →'}
          </button>
          {showEvidence && (
            <pre className="evidence-strip">{JSON.stringify(answer.evidence_used, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  );
}
