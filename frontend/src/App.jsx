import { useEffect } from "react";
import { Row, Col } from "react-bootstrap";
import { Toaster, toast } from "react-hot-toast";
import FarmForm from "./components/FarmForm.jsx";
import RecommendationCard from "./components/RecommendationCard.jsx";
import AskBox from "./components/AskBox.jsx";
import ContextualLoader from "./components/ContextualLoader.jsx";
import {
  useAgriPulseStore,
  useReportWorkflow,
} from "./store/useAgriPulseStore.js";
import fieldImage from "./assets/greenish_field.jpg";

export default function App() {
  const { report, farmId, loading, error } = useAgriPulseStore();
  const { generateReport } = useReportWorkflow();

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  return (
    <div className="app" style={{ "--field-image": `url(${fieldImage})` }}>
      <Toaster
        position="top-right"
        toastOptions={{ className: "agripulse-toast" }}
      />
      <header className="header">
        <div>
          <h1>
            <span className="agri">Agri</span>
            <span className="pulse-p">P</span>
            <span className="pulse-u">u</span>
            <span className="pulse-l">l</span>
            <span className="pulse-s">s</span>
            <span className="pulse-e">e</span>
          </h1>
          <div className="tagline">
            From fragmented farm data to explainable decisions
          </div>
        </div>
      </header>

      <FarmForm onSubmit={generateReport} loading={loading} />

      {loading && !report && <ContextualLoader mode="report" />}

      {report && (
        <section aria-live="polite">
          <h2 className="report-heading">
            Today's Farm Intelligence - {report.crop} 📍 {report.district}
          </h2>
          {report.recommendations.length === 0 ? (
            <div className="empty-state">
              No signals require attention right now.
            </div>
          ) : (
            <Row className="recommendation-list">
              {report.recommendations.map((rec, i) => (
                <Col xs={12} key={i}>
                  <RecommendationCard rec={rec} crop={report.crop} index={i} />
                </Col>
              ))}
            </Row>
          )}
          <AskBox farmId={farmId} />
        </section>
      )}
    </div>
  );
}
