import { useState } from 'react';
import FarmForm from './components/FarmForm.jsx';
import RecommendationCard from './components/RecommendationCard.jsx';
import AskBox from './components/AskBox.jsx';
import { api } from './api.js';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [farmId, setFarmId] = useState(null);

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const farm = await api.createFarm(formData);
      setFarmId(farm.farm_id);
      const intelligence = await api.getIntelligence(farm.farm_id);
      setReport(intelligence);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Agri<span className="mark">Pulse</span></h1>
          <div className="tagline">From fragmented farm data to explainable decisions</div>
        </div>
      </header>

      <FarmForm onSubmit={handleGenerate} loading={loading} />

      {error && <div className="status-text error">Error: {error}</div>}

      {report && (
        <section>
          <h2 className="report-heading">
            Today's Farm Intelligence — {report.crop} · {report.district}
          </h2>
          {report.recommendations.length === 0 ? (
            <div className="empty-state">No signals require attention right now.</div>
          ) : (
            report.recommendations.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} />
            ))
          )}
          <AskBox farmId={farmId} />
        </section>
      )}

      {!report && !loading && !error && (
        <div className="status-text">Fill in a farm profile above and generate today's report.</div>
      )}
    </div>
  );
}
