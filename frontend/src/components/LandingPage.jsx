import { motion } from "framer-motion";
import { Col, Container, Row } from "react-bootstrap";
import { useAgriPulseStore } from "../store/useAgriPulseStore.js";

const FEATURES = [
  {
    icon: "💧",
    title: "Smart Irrigation Guidance",
    description:
      "Optimizes water usage using real-time soil moisture and microclimate data.",
  },
  {
    icon: "📈",
    title: "Market Timing Insights",
    description:
      "Tracks crop price fluctuations and market arrivals to maximize revenue.",
  },
  {
    icon: "🛡️",
    title: "Early Crop Risk Alerts",
    description:
      "Identifies pest threats and weather risks before yield is impacted.",
  },
];

export default function LandingPage() {
  const getStarted = useAgriPulseStore((state) => state.getStarted);

  return (
    <motion.main
      className="landing-page"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
    >
      <Container>
        <div className="landing-kicker">
          {" "}
          Agricultural Decision Intelligence Platform
        </div>
        <Row as="header" className="landing-hero align-items-end">
          <Col>
            <h1 className="landing-brand">
              <span className="agri">Farm</span>
              <span className="pulse-p">P</span>
              <span className="pulse-u">u</span>
              <span className="pulse-l">l</span>
              <span className="pulse-s">s</span>
              <span className="pulse-e">e</span>
            </h1>
            <p className="landing-tagline">
              From Fragmented Farm Data to Explainable Decisions
            </p>
          </Col>
          <Col xs="auto">
            <span className="landing-status">● Evidence-first</span>
          </Col>
        </Row>

        <Row
          as="section"
          className="landing-intro align-items-center"
          aria-labelledby="landing-intro-title"
        >
          <Col lg={8}>
            <p id="landing-intro-title">
              FarmPulse merges soil metrics, local market trends, and AI-driven
              weather analysis into actionable farm intelligence. Make
              confident, evidence-first decisions with transparent signals
              tailored to your field.
            </p>
          </Col>
          <Col lg={4} className="text-lg-end">
            <motion.button
              className="landing-cta"
              type="button"
              onClick={getStarted}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.98 }}
            >
              Generate Farm Intelligence <span aria-hidden="true">→</span>
            </motion.button>
          </Col>
        </Row>

        <Row
          as="section"
          className="landing-features"
          aria-label="FarmPulse features"
        >
          {FEATURES.map((feature, index) => (
            <Col md={4} key={feature.title}>
              <motion.article
                className="landing-feature-card"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.12 + index * 0.08, duration: 0.4 }}
                whileHover={{ y: -5 }}
              >
                <div className="landing-feature-icon" aria-hidden="true">
                  {feature.icon}
                </div>
                <h2>{feature.title}</h2>
                <p>{feature.description}</p>
              </motion.article>
            </Col>
          ))}
        </Row>

        <div className="landing-data-tag">
          LOCALIZED · EXPLAINABLE · ACTIONABLE
        </div>
      </Container>
    </motion.main>
  );
}
