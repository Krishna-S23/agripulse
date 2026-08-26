import { useEffect } from "react";
import { Row, Col } from "react-bootstrap";
import { Toaster, toast } from "react-hot-toast";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import FarmForm from "./components/FarmForm.jsx";
import RecommendationCard from "./components/RecommendationCard.jsx";
import AskBox from "./components/AskBox.jsx";
import {
  useAgriPulseStore,
  useReportWorkflow,
} from "./store/useAgriPulseStore.js";

export default function App() {
  const { report, farmId, loading, error } = useAgriPulseStore();
  const { generateReport } = useReportWorkflow();

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  return (
    <div className="app">
      <Toaster
        position="top-right"
        toastOptions={{ className: "agripulse-toast" }}
      />
      <header className="header">
        <div>
          <h1>
            Agri<span className="mark">Pulse</span>
          </h1>
          <div className="tagline">
            From fragmented farm data to explainable decisions
          </div>
        </div>
      </header>

      <FarmForm onSubmit={generateReport} loading={loading} />

      {loading && (
        <div
          className="report-skeleton"
          aria-label="Loading farm intelligence"
          aria-live="polite"
        >
          {[1, 2, 3].map((item) => (
            <Skeleton key={item} height={148} className="skeleton-card" />
          ))}
        </div>
      )}

      {report && (
        <section aria-live="polite">
          <h2 className="report-heading">
            Today's Farm Intelligence — {report.crop} · {report.district}
          </h2>
          {report.recommendations.length === 0 ? (
            <div className="empty-state">
              No signals require attention right now.
            </div>
          ) : (
            <Row className="recommendation-list">
              {report.recommendations.map((rec, i) => (
                <Col xs={12} key={i}>
                  <RecommendationCard rec={rec} index={i} />
                </Col>
              ))}
            </Row>
          )}
          <AskBox farmId={farmId} />
        </section>
      )}

      {!report && !loading && !error && (
        <div className="status-text">
          Fill in a farm profile above and generate today's report.
        </div>
      )}
    </div>
  );
}
