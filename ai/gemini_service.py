import os
import logging
import requests
from ai.base_ai_service import BaseAIService
import ai.ai_prompts as ai_prompts
import response_parser

logger = logging.getLogger(__name__)

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent"


class GeminiService(BaseAIService):
    def __init__(self, api_key):
        self.api_key = api_key

    def _generate(self, prompt, json_mode=False):
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if json_mode:
            body["generationConfig"] = {"responseMimeType": "application/json"}
        resp = requests.post(f"{_API_URL}?key={self.api_key}", json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("candidates") or []
        if not candidates:
            reason = (data.get("promptFeedback") or {}).get("blockReason", "no candidates")
            raise RuntimeError(f"Gemini returned no candidates: {reason}")

        cand = candidates[0]
        finish = cand.get("finishReason")
        if finish and finish not in ("STOP", "MAX_TOKENS"):
            raise RuntimeError(f"Gemini finishReason={finish}")

        parts = ((cand.get("content") or {}).get("parts")) or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned empty text")
        return text

    def summarize_with_emojis(self, article_text, target_language='en'):
        prompt = ai_prompts.get_summarize_with_emojis_prompt(target_language)
        text = self._generate(f"{prompt}\n\n{article_text}")
        return response_parser.parse_summary_with_emojis(text)

    def evaluate_article(self, article_text):
        prompt = ai_prompts.get_evaluate_article_prompt()
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "article_evaluation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "expat_impact": {"type": "integer", "minimum": 1, "maximum": 10, "description": "How relevant or impactful the news is for expatriates (1-10)"},
                        "event_weight": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Significance or uniqueness of the event (1-10)"},
                        "politics": {"type": "integer", "minimum": 0, "maximum": 10, "description": "Non-political/innovation score (0=political, 10=non-political/innovative)"},
                        "timeliness": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Time-sensitivity or urgency (1-10)"},
                        "practical_utility": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Usefulness for reader's daily life (1-10)"}
                    },
                    "required": ["expat_impact", "event_weight", "politics", "timeliness", "practical_utility"],
                    "additionalProperties": False
                }
            }
        }
        full_prompt = f"{prompt} Provide a JSON response with the following schema: {response_format}\n\n{article_text}"
        text = self._generate(full_prompt, json_mode=True)
        logger.debug(f"Gemini evaluate response: {text}")
        return response_parser.parse_evaluate_article(text)
