import requests
from ai.base_ai_service import BaseAIService
import ai.ai_prompts as ai_prompts
import response_parser

_API_URL = "http://localhost:1234/v1/chat/completions"


class OpenAIService(BaseAIService):
    def __init__(self):
        self.headers = {"Authorization": "Bearer lm-studio", "Content-Type": "application/json"}

    def _chat(self, messages, response_format={"type": "text"}, model="microsoft/phi-4-reasoning-plus"):
        body = {"model": model, "messages": messages, "response_format": response_format, "temperature": 0.7}
        resp = requests.post(_API_URL, json=body, headers=self.headers, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def summarize_with_emojis(self, article_text, target_language='en'):
        messages = [
            {"role": "system", "content": ai_prompts.get_summarize_with_emojis_prompt(target_language)},
            {"role": "user", "content": article_text}
        ]
        return response_parser.parse_summary_with_emojis(self._chat(messages))

    def evaluate_article(self, article_text):
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
        messages = [
            {"role": "system", "content": ai_prompts.get_evaluate_article_prompt()},
            {"role": "user", "content": article_text}
        ]
        return response_parser.parse_evaluate_article(self._chat(messages, response_format=response_format))
