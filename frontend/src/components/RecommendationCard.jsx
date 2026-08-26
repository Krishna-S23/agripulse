import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Droplets, Sprout, TrendingUp } from "lucide-react";

const CONFIDENCE_LEVELS = { LOW: 1, MEDIUM: 2, HIGH: 3 };

const TITLES = {
  DELAY_IRRIGATION: "Delay irrigation",
  IRRIGATE_NOW: "Irrigate now",
  MONITOR: "Monitor before irrigating",
  CONSIDER_SELLING: "Consider selling",
  HOLD_AND_MONITOR: "Hold and monitor market",
  MONITOR_MARKET: "Monitor the market",
  MONITOR_CROP_CONDITION: "Monitor crop condition",
};

const TYPE_ICONS = {
  IRRIGATION: Droplets,
  MARKET: TrendingUp,
  CROP_RISK: Sprout,
};

export default function RecommendationCard({ rec, index = 0 }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const filledDots = CONFIDENCE_LEVELS[rec.confidence] || 1;
  const TypeIcon = TYPE_ICONS[rec.recommendation_type] || Sprout;

  return (
    <motion.div
      className="rec-card"
      data-type={rec.recommendation_type}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      whileHover={{
        y: -4,
        scale: 1.01,
        boxShadow: "0 12px 24px rgba(28, 42, 31, 0.14)",
      }}
    >
      <div className="rec-top">
        <div>
          <div className="rec-label">
            <TypeIcon className="rec-type-icon" size={16} aria-hidden="true" />
            {rec.recommendation_type.replace("_", " ")}
          </div>
          <div className="rec-title">
            {TITLES[rec.recommendation] || rec.recommendation}
          </div>
        </div>
        <div
          className="confidence-dots"
          title={`Confidence: ${rec.confidence}`}
        >
          {[1, 2, 3].map((i) => (
            <span
              key={i}
              className={`dot ${i <= filledDots ? "filled" : ""}`}
            />
          ))}
          {rec.confidence}
        </div>
      </div>

      <p className="rec-explanation">{rec.explanation}</p>

      <button
        className="evidence-toggle"
        onClick={() => setShowEvidence(!showEvidence)}
      >
        {showEvidence ? "Hide supporting data" : "View supporting data →"}
      </button>

      <AnimatePresence initial={false}>
        {showEvidence && (
          <motion.div
            className="evidence-strip"
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: "auto", marginTop: "0.75rem" }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.22 }}
          >
            {rec.evidence.map((e, i) => (
              <div key={i}>{e}</div>
            ))}
            {rec.risk_signals &&
              rec.risk_signals.map((r, i) => (
                <div key={`r${i}`}>risk: {r}</div>
              ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
