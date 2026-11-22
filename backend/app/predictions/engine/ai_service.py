"""Provider-agnostic LLM check, review and English writing via any OpenAI-compatible API
(Groq, Google Gemini via OpenAI-compat endpoint, OpenRouter, local Ollama, etc.).

PRIVACY: only anonymized astrological factor evidence is transmitted (no client name,
birth date/time, or coordinates).
"""

import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("astro_app.predictions.ai")

# Runtime in-memory overrides for AI settings
_runtime_config: Dict[str, str] = {
    "provider": "",
    "base_url": "",
    "api_key": "",
    "model": "",
}

PROVIDER_DEFAULTS = {
    "groq": {
        "name": "Groq Cloud (Fast & Free Tier)",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
    },
    "gemini": {
        "name": "Google Gemini (Free Tier)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        "default_model": "gemini-1.5-flash",
        "env_key": "GEMINI_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter (Free Tier Models)",
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["meta-llama/llama-3.3-70b-instruct:free", "google/gemini-2.0-flash-exp:free"],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "env_key": "OPENROUTER_API_KEY",
    },
    "custom": {
        "name": "Custom / Local OpenAI-Compatible",
        "base_url": "",
        "models": ["default"],
        "default_model": "default",
        "env_key": "AI_API_KEY",
    },
}


def get_ai_config() -> Dict[str, Any]:
    """Resolve active AI configuration from runtime settings or environment variables."""
    # 1. Check runtime overrides
    provider = _runtime_config.get("provider", "").lower()
    base_url = _runtime_config.get("base_url", "")
    api_key = _runtime_config.get("api_key", "")
    model = _runtime_config.get("model", "")

    # 2. If not explicitly set in runtime, check environment variables
    if not api_key:
        if os.getenv("GROQ_API_KEY"):
            provider = provider or "groq"
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["groq"]["base_url"]
            model = model or PROVIDER_DEFAULTS["groq"]["default_model"]
        elif os.getenv("GEMINI_API_KEY"):
            provider = provider or "gemini"
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["gemini"]["base_url"]
            model = model or PROVIDER_DEFAULTS["gemini"]["default_model"]
        elif os.getenv("OPENROUTER_API_KEY"):
            provider = provider or "openrouter"
            api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["openrouter"]["base_url"]
            model = model or PROVIDER_DEFAULTS["openrouter"]["default_model"]
        elif os.getenv("AI_API_KEY"):
            provider = provider or "custom"
            api_key = os.getenv("AI_API_KEY", "").strip()
            base_url = base_url or os.getenv("AI_BASE_URL", "").strip()
            model = model or os.getenv("AI_MODEL", "").strip() or "default"

    if provider in PROVIDER_DEFAULTS and not base_url:
        base_url = PROVIDER_DEFAULTS[provider]["base_url"]
    if provider in PROVIDER_DEFAULTS and not model:
        model = PROVIDER_DEFAULTS[provider]["default_model"]

    is_configured = bool(api_key and base_url and model)

    return {
        "is_configured": is_configured,
        "provider": provider or "none",
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "timeout": 45,
    }


def update_runtime_ai_config(provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Update runtime AI settings dynamically."""
    global _runtime_config
    if provider is not None:
        _runtime_config["provider"] = provider.lower()
        if provider.lower() in PROVIDER_DEFAULTS and not base_url:
            _runtime_config["base_url"] = PROVIDER_DEFAULTS[provider.lower()]["base_url"]
    if model is not None:
        _runtime_config["model"] = model
    if api_key is not None:
        _runtime_config["api_key"] = api_key.strip()
    if base_url is not None:
        _runtime_config["base_url"] = base_url.strip()
    return get_ai_config()


def list_providers_status() -> Dict[str, Any]:
    """List available providers, their configured status and available models."""
    cfg = get_ai_config()
    providers_info = []
    for pid, pdata in PROVIDER_DEFAULTS.items():
        env_val = os.getenv(pdata["env_key"], "")
        has_env_key = bool(env_val.strip())
        is_active = (cfg["provider"] == pid and cfg["is_configured"])
        providers_info.append({
            "id": pid,
            "name": pdata["name"],
            "models": pdata["models"],
            "default_model": pdata["default_model"],
            "has_key": has_env_key or (cfg["provider"] == pid and bool(cfg["api_key"])),
            "is_active": is_active,
        })
    return {
        "active_provider": cfg["provider"],
        "active_model": cfg["model"],
        "is_configured": cfg["is_configured"],
        "providers": providers_info,
    }


def call_llm_chat(messages: List[Dict[str, str]], retries: int = 2) -> str:
    """Call the OpenAI-compatible chat completion endpoint."""
    cfg = get_ai_config()
    if not cfg["is_configured"]:
        raise RuntimeError("No AI API is currently configured. Provide an API key.")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    # OpenRouter specific optional headers
    if "openrouter" in cfg["base_url"]:
        headers["HTTP-Referer"] = "https://astro-workspace.local"
        headers["X-Title"] = "Astro Workspace"

    payload_dict: Dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.25,
    }

    body = json.dumps(payload_dict).encode("utf-8")

    last_error = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=cfg["timeout"]) as response:
                resp_text = response.read().decode("utf-8")
                resp_json = json.loads(resp_text)
                return resp_json["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as err:
            last_error = err
            err_body = ""
            try:
                err_body = err.read().decode("utf-8")
            except Exception:
                pass
            logger.warning(f"AI API HTTP {err.code} on attempt {attempt+1}: {err_body}")
            if err.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"AI API request failed (HTTP {err.code}): {err_body[:200]}") from err
        except Exception as ex:
            last_error = ex
            logger.warning(f"AI API error on attempt {attempt+1}: {ex}")
            if attempt < retries:
                time.sleep(2)
                continue
            raise RuntimeError(f"AI API call failed: {ex}") from ex

    raise RuntimeError(f"AI call failed after retries: {last_error}")


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Safely extract and parse JSON object from LLM response text."""
    clean = raw_text.strip()
    # Strip markdown code blocks
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
    clean = clean.strip()

    match = re.search(r"\{[\s\S]*\}", clean)
    if match:
        clean = match.group(0)

    return json.loads(clean)


REVIEW_SYSTEM_PROMPT = """You are an expert Jyotish editor and validation assistant for an authentic Vedic astrology prediction report.
Your role is to review structured astrological evidence from a natal chart and produce a comprehensive, professional English interpretation.

CRITICAL CONSTRAINTS:
1. Grounding: You may ONLY use the planetary placements, house lordships, dignities, yogas and dasha timing provided in the EVIDENCE. Do NOT invent missing planets, aspects, yogas, or life events.
2. Non-deterministic Language: Vedic Jyotish is symbolic and indicative. Never use deterministic or fatalistic phrases (e.g., 'you will definitely become rich', 'divorce is certain', 'guaranteed success'). Use hedged, constructive phrasing (e.g., 'traditionally interpreted as indicating', 'suggests potential for', 'may experience periods of', 'fosters disciplined effort towards').
3. No Forbidden Content: Strictly NEVER produce medical diagnoses, illness cures, death predictions, guaranteed wealth amounts, or legal/visa guarantees.
4. Explanations: Explain any technical Sanskrit term naturally in plain English (e.g. Kendra = pivotal angle houses; Trikona = trine houses).
5. Citations: Maintain citations of relevant [RULE-ID] tags where applicable.

You must respond STRICTLY with valid JSON following this schema:
{
  "topic": "<topic title>",
  "status": "reviewed",
  "summary": "<2-3 sentence executive summary of the combined indications>",
  "prediction": "<Full professional narrative with paragraphs: Tendencies & Themes, Supporting Influences, Challenges & Growth Areas, Timing & Guidance>",
  "supporting_factors": [
    {
      "factor": "<chart factor>",
      "interpretation": "<how it is traditionally interpreted>",
      "rule_id": "<RULE-ID>"
    }
  ],
  "challenging_factors": [
    {
      "factor": "<modifying factor>",
      "interpretation": "<constructive meaning of the challenge>",
      "rule_id": "<RULE-ID>"
    }
  ],
  "counter_indicators": [],
  "timing": ["<summary of relevant active dasha activations if present>"],
  "validation": {
    "rulebook_consistency": "reviewed",
    "chart_evidence_consistency": "verified",
    "unsupported_claims": [],
    "contradictions": [],
    "missing_data": [],
    "warnings": []
  },
  "limitations": [
    "Symbolic interpretation based on classical Parashari principles; not deterministic certainty."
  ]
}
"""


def ai_review_section(
    topic: str,
    title: str,
    evidence_items: List[Dict[str, Any]],
    timing_items: List[Dict[str, Any]],
    templated_draft: str,
) -> Tuple[Dict[str, Any], str, List[str]]:
    """Run Stage 3 (AI Validation) and Stage 4 (Correction / Structured Output).
    Returns (structured_dict, final_prediction_text, validation_notes).
    """
    notes: List[str] = []
    
    anonymized_evidence = [
        {
            "rule_id": e.get("rule_id"),
            "kind": e.get("kind"),
            "planets": e.get("planets"),
            "houses": e.get("houses"),
            "direction": e.get("direction"),
            "text": e.get("text"),
        }
        for e in evidence_items
    ]

    timing_summary = [
        {
            "level": t.get("timing", {}).get("level"),
            "lord": t.get("timing", {}).get("lord"),
            "start": t.get("timing", {}).get("start"),
            "end": t.get("timing", {}).get("end"),
            "text": t.get("text"),
        }
        for t in timing_items if "timing" in t
    ]

    user_payload = {
        "topic": topic,
        "title": title,
        "evidence": anonymized_evidence,
        "timing": timing_summary,
        "baseline_draft": templated_draft,
    }

    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    try:
        raw_response = call_llm_chat(messages)
        parsed = parse_llm_json(raw_response)
        
        # Verify required keys
        if "prediction" in parsed and parsed.get("status") in ("reviewed", "ai_rewritten_audited"):
            prediction_text = parsed["prediction"]
            return parsed, prediction_text, notes
        else:
            notes.append("AI response missing expected JSON fields; fell back to rule draft.")
    except Exception as exc:
        logger.error(f"AI review error for topic '{topic}': {exc}")
        notes.append(f"AI review failed ({exc}); used verified rulebook draft.")

    return {}, templated_draft, notes
