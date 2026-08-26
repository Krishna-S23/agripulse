import { motion } from "framer-motion";
import { Droplets, Sprout, TrendingUp } from "lucide-react";

const REPORT_STEPS = [
  {
    type: "IRRIGATION",
    label: "Checking Water Data...",
    Icon: Droplets,
    color: "var(--sky)",
  },
  {
    type: "CROP_RISK",
    label: "Reviewing Crop Health...",
    Icon: Sprout,
    color: "var(--plum)",
  },
  {
    type: "MARKET",
    label: "Analyzing Markets...",
    Icon: TrendingUp,
    color: "var(--gold)",
  },
];

export default function ContextualLoader({ mode = "report" }) {
  const steps =
    mode === "ask"
      ? [REPORT_STEPS[0], REPORT_STEPS[1], REPORT_STEPS[2]]
      : REPORT_STEPS;

  return (
    <div
      className={`contextual-loader ${mode === "ask" ? "contextual-loader-ask" : ""}`}
      aria-live="polite"
      aria-busy="true"
    >
      <div className="contextual-loader-track" role="status">
        {steps.map(({ type, label, Icon, color }, index) => (
          <motion.div
            className="contextual-step"
            data-type={type}
            key={type}
            initial={{ opacity: 0.35, scale: 0.92 }}
            animate={{ opacity: [0.35, 1, 0.35], scale: [0.92, 1, 0.92] }}
            transition={{
              duration: 1.8,
              delay: index * 0.3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <motion.span
              className="contextual-icon"
              style={{ color }}
              animate={
                type === "IRRIGATION"
                  ? { y: [0, 4, 0] }
                  : type === "CROP_RISK"
                    ? { scale: [0.9, 1.08, 0.9] }
                    : { y: [2, -3, 2] }
              }
              transition={{
                duration: 1.4,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <Icon aria-hidden="true" size={28} strokeWidth={1.8} />
            </motion.span>
            <span>{label}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
