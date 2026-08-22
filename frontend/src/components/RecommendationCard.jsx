import { useState } from 'react';

const CONFIDENCE_LEVELS = { LOW: 1, MEDIUM: 2, HIGH: 3 };

const TITLES = {
  DELAY_IRRIGATION: 'Delay irrigation',
  IRRIGATE_NOW: 'Irrigate now',
  MONITOR: 'Monitor before irrigating',
  CONSIDER_SELLING: 'Consider selling',
  HOLD_AND_MONITOR: 'Hold and monitor market',
  MONITOR_MARKET: 'Monitor the market',
  MONITOR_CROP_CONDITION: 'Monitor crop condition',
};

export default function RecommendationCard({ rec }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const filledDots = CONFIDENCE_LEVELS[rec.confidence] || 1;

  return (
    <div className="rec-card" data-type={rec.recommendation_type}>
      <div className="rec-top">
        <div>
          <div className="rec-label">{rec.recommendation_type.replace('_', ' ')}</div>
          <div className="rec-title">{TITLES[rec.recommendation] || rec.recommendation}</div>
        </div>
        <div className="confidence-dots" title={`Confidence: ${rec.confidence}`}>
          {[1, 2, 3].map((i) => (
            <span key={i} className={`dot ${i <= filledDots ? 'filled' : ''}`} />
          ))}
          {rec.confidence}
        </div>
      </div>

      <p className="rec-explanation">{rec.explanation}</p>

      <button className="evidence-toggle" onClick={() => setShowEvidence(!showEvidence)}>
        {showEvidence ? 'Hide supporting data' : 'View supporting data →'}
      </button>

      {showEvidence && (
        <div className="evidence-strip">
          {rec.evidence.map((e, i) => <div key={i}>{e}</div>)}
          {rec.risk_signals && rec.risk_signals.map((r, i) => <div key={`r${i}`}>risk: {r}</div>)}
        </div>
      )}
    </div>
  );
}
