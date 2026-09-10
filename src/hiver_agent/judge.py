from __future__ import annotations

import json
import os
import urllib.request

from .agent import Prediction
from .evaluate import judge_rubric


def build_prompt(text: str, prediction: Prediction) -> str:
    return json.dumps({
        "task": "Grade a customer support reply. Do not reward factual claims unsupported by evidence.",
        "customer_message": text,
        "candidate": prediction.reply,
        "historical_evidence": prediction.evidence,
        "rubric": judge_rubric(),
        "output_schema": {"grounding": 1, "helpfulness": 1, "tone": 1, "safety": 1, "rationale": "string"},
    })


def score_with_openai(text: str, prediction: Prediction, model: str = "gpt-4o-mini") -> dict:
    """Call the OpenAI-compatible Responses API without adding a runtime dependency."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for the optional LLM judge")
    payload = json.dumps({
        "model": model,
        "input": build_prompt(text, prediction),
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = json.loads(response.read())
    output = body.get("output_text")
    if not output:
        output = body["output"][0]["content"][0]["text"]
    return json.loads(output)
