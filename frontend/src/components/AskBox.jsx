import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  useAgriPulseStore,
  useAskWorkflow,
} from "../store/useAgriPulseStore.js";
import ContextualLoader from "./ContextualLoader.jsx";

export default function AskBox({ farmId }) {
  const [question, setQuestion] = useState("");
  const [showEvidence, setShowEvidence] = useState(false);
  const answer = useAgriPulseStore((state) => state.askAnswer);
  const error = useAgriPulseStore((state) => state.error);
  const { askQuestion, loading } = useAskWorkflow();

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    askQuestion(question.trim());
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
        <button
          className="btn-primary btn-small"
          type="submit"
          disabled={loading}
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      {loading && <ContextualLoader mode="ask" />}

      <AnimatePresence>
        {answer && (
          <motion.div
            className="ask-answer"
            aria-live="polite"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
          >
            <p className="rec-explanation">{answer.answer}</p>
            <button
              className="evidence-toggle"
              onClick={() => setShowEvidence(!showEvidence)}
            >
              {showEvidence ? "Hide evidence used" : "View evidence used →"}
            </button>
            {showEvidence && (
              <pre className="evidence-strip">
                {JSON.stringify(answer.evidence_used, null, 2)}
              </pre>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
