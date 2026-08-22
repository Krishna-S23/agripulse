"""
AgriPulse Orchestrator.

Flow:
  farm profile -> call relevant agents -> Decision Engine (rules) ->
  Gemini (explains + phrases the already-decided recommendations) -> response

Gemini NEVER invents the recommendation — it only explains evidence that the
Decision Engine already produced. This keeps every output auditable.

Uses google-generativeai (Gemini API, API-key based) for simplicity. If you
prefer Vertex AI / ADK's native model routing, swap `_call_gemini` for a
`vertexai.generative_models.GenerativeModel` call — same prompt, same
contract (must return plain text).

If GEMINI_API_KEY is not set, falls back to a template-based explanation so
the whole pipeline still runs end-to-end without any LLM credentials.
"""
import os
import json
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

from weather_agent import get_weather_signal
from soil_agent import get_soil_signal
from market_agent import get_market_signal
from decision_engine import build_recommendations

logger = logging.getLogger("agripulse.orchestrator")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

_RECOMMENDATION_COPY = {
    "DELAY_IRRIGATION": "Consider delaying irrigation",
    "IRRIGATE_NOW": "Irrigation is recommended now",
    "MONITOR": "Monitor conditions before deciding on irrigation",
    "CONSIDER_SELLING": "Current market conditions favor selling",
    "HOLD_AND_MONITOR": "Consider holding and monitoring the market",
    "MONITOR_MARKET": "Keep monitoring the market",
    "MONITOR_CROP_CONDITION": "Monitor crop conditions closely",
}


def get_today_intelligence(farm: dict) -> dict:
    """Main entry point: given a farm profile dict (farm_id, district, crop),
    returns the full prioritized intelligence report."""
    district = farm["district"]
    crop = farm["crop"]
    farm_id = farm["farm_id"]

    weather = get_weather_signal(district)
    soil = get_soil_signal(farm_id)
    market = get_market_signal(crop, district)

    recommendations = build_recommendations(weather, soil, market)

    for rec in recommendations:
        rec["explanation"] = _explain(rec, farm)

    return {
        "farm_id": farm_id,
        "district": district,
        "crop": crop,
        "recommendations": recommendations,
        "raw_signals": {"weather": weather, "soil": soil, "market": market},
    }


def answer_question(farm: dict, question: str) -> dict:
    """Handles free-text questions by routing to the relevant agents based
    on keyword matching, then asking Gemini to answer using only that
    evidence. Simple deterministic routing keeps this auditable too — no
    LLM-driven tool selection for the MVP."""
    q = question.lower()
    evidence = {}

    if any(k in q for k in ["irrigat", "water", "rain", "soil"]):
        evidence["weather"] = get_weather_signal(farm["district"])
        evidence["soil"] = get_soil_signal(farm["farm_id"])
    if any(k in q for k in ["market", "price", "sell"]):
        evidence["market"] = get_market_signal(farm["crop"], farm["district"])
    if not evidence:
        # default: pull everything if we can't route confidently
        evidence["weather"] = get_weather_signal(farm["district"])
        evidence["soil"] = get_soil_signal(farm["farm_id"])
        evidence["market"] = get_market_signal(farm["crop"], farm["district"])

    answer = _call_gemini(_build_qa_prompt(question, evidence))
    return {"question": question, "answer": answer, "evidence_used": evidence}


def _explain(rec: dict, farm: dict) -> str:
    prompt = _build_explanation_prompt(rec, farm)
    return _call_gemini(prompt)


def _build_explanation_prompt(rec: dict, farm: dict) -> str:
    return f"""You are AgriPulse, an agricultural decision-support assistant.
A rule-based decision engine has already produced the recommendation below
for a farmer's field. Your job is ONLY to explain it clearly in 2-3 plain
sentences, in simple language a farmer would understand. Do not change the
recommendation or invent any numbers not in the evidence.

Farm: {farm.get('crop')} in {farm.get('district')}, growth stage {farm.get('growth_stage', 'unknown')}
Recommendation type: {rec['recommendation_type']}
Decision: {rec['recommendation']}
Confidence: {rec['confidence']}
Evidence: {json.dumps(rec['evidence'])}

Write the explanation now:"""


def _build_qa_prompt(question: str, evidence: dict) -> str:
    return f"""You are AgriPulse, an agricultural decision-support assistant.
Answer the farmer's question using ONLY the evidence below. If the evidence
doesn't fully answer it, say what's missing rather than guessing.

Question: {question}
Evidence: {json.dumps(evidence, indent=2)}

Answer in 2-4 plain sentences:"""


def _call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    model_name = os.environ.get("GEMINI_MODEL") or GEMINI_MODEL or "gemini-3.6-flash"
    if not api_key:
        return _fallback_explanation(prompt)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:  # noqa: BLE001 - degrade gracefully in a demo
        logger.error("Gemini call failed (model=%s), falling back to template: %s", model_name, e)
        return _fallback_explanation(prompt)


def _fallback_explanation(prompt: str) -> str:
    """Used when no GEMINI_API_KEY is set, or the API call fails — keeps the
    demo alive even if the LLM is unavailable."""
    return ("[Template explanation — set GEMINI_API_KEY for full natural-language "
            "output] Based on current evidence, please review the flagged data points "
            "for this recommendation.")


if __name__ == "__main__":
    sample_farm = {
        "farm_id": "F001",
        "district": "Coimbatore",
        "crop": "Tomato",
        "growth_stage": "Flowering",
    }
    result = get_today_intelligence(sample_farm)
    print(json.dumps(result, indent=2))
