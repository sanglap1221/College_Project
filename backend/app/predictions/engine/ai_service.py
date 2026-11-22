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
from typing import Any, Dict, List, Optional

from .writer import enforce_topic_json_limits

logger = logging.getLogger("astro_app.predictions.ai")

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
        "models": ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "openai/gpt-oss-120b",
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
    provider = _runtime_config.get("provider", "").lower()
    base_url = _runtime_config.get("base_url", "")
    api_key = _runtime_config.get("api_key", "")
    model = _runtime_config.get("model", "")

    if not api_key:
        if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY").strip():
            provider = provider or "gemini"
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["gemini"]["base_url"]
            model = model or PROVIDER_DEFAULTS["gemini"]["default_model"]
        elif os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_API_KEY").strip():
            provider = provider or "openrouter"
            api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["openrouter"]["base_url"]
            model = model or PROVIDER_DEFAULTS["openrouter"]["default_model"]
        elif os.getenv("GROQ_API_KEY"):
            provider = provider or "groq"
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            base_url = base_url or PROVIDER_DEFAULTS["groq"]["base_url"]
            model = model or PROVIDER_DEFAULTS["groq"]["default_model"]
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
    cfg = get_ai_config()
    if not cfg["is_configured"]:
        raise RuntimeError("No AI API is currently configured. Provide an API key.")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    if "openrouter" in cfg["base_url"]:
        headers["HTTP-Referer"] = "https://astro-workspace.local"
        headers["X-Title"] = "Astro Workspace"

    payload_dict: Dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.2,
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
    clean = raw_text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
    clean = clean.strip()
    match = re.search(r"\{[\s\S]*\}", clean)
    if match:
        clean = match.group(0)
    return json.loads(clean)


BATCH_GEN_PROMPT = """You are an expert Vedic Jyotish editor.
Your task is to write structured predictions for several life topics simultaneously based ONLY on the provided astrological factors.

CRITICAL RULES:
1. Grounding: You may ONLY use the planetary placements, house lordships, dignities, yogas and dasha timing provided in the EVIDENCE for each topic. Do not invent missing facts.
2. Non-deterministic Language: Vedic Jyotish is symbolic and indicative. Never use fatalistic statements.
3. Health Area: Strictly non-diagnostic traditional constitution/element symbolism.
4. Schema per topic:
   - "overview": string, 40 to 70 words.
   - "themes": array of exactly 3 strings, each <= 18 words.
   - "challenges": array of exactly 2 strings, each <= 22 words.
   - "basis_ids": array of rule IDs strictly chosen from the topic's allowed_ids.

Output STRICTLY a valid JSON object matching:
{
  "topics": {
    "<topic_key>": {
      "overview": "...",
      "themes": ["...", "...", "..."],
      "challenges": ["...", "..."],
      "basis_ids": ["..."]
    }
  }
}
"""

BATCH_AUDIT_PROMPT = """You are a strict compliance auditor for a Vedic Jyotish report.
Review the interpretations produced for each topic against classical grounding rules.
Flag any topic containing:
- Fatalistic or deterministic claims
- Medical diagnoses or health prescriptions
- Unsupported planetary claims
Output STRICTLY valid JSON:
{
  "all_passed": true,
  "rejected_topics": [],
  "notes": []
}
"""


def ai_generate_and_audit_all_topics(
    topics_packages: Dict[str, Any],
    dasha_summary: List[Dict[str, Any]],
    language: str = "en",
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Generate all topics in ONE AI call and audit all topics in ONE call (free-tier rate limits).
    Returns (topic_results_map, audit_notes).
    """
    notes: List[str] = []
    compact_input = {
        "target_language": language,
        "active_dashas": dasha_summary,
        "topics": {},
    }

    for topic, pkg in topics_packages.items():
        compact_input["topics"][topic] = {
            "title": pkg["title"],
            "evidence": [
                {
                    "rule_id": e.get("rule_id"),
                    "direction": e.get("direction"),
                    "text": e.get("text"),
                }
                for e in pkg["used_items"]
            ],
            "allowed_ids": sorted(list(pkg["allowed_ids"]))[:8],
        }

    lang_instruction = "Write all text strictly in clear, professional English."
    if language == "bn":
        lang_instruction = "CRITICAL REQUIREMENT: Write all 'overview', 'themes', and 'challenges' strictly in fluent, dignified Bengali (বাংলা). Do NOT output English prose for the content."
    elif language == "hi":
        lang_instruction = "CRITICAL REQUIREMENT: Write all 'overview', 'themes', and 'challenges' strictly in fluent, dignified Hindi (हिन्दी). Do NOT output English prose for the content."

    batch_gen_prompt = BATCH_GEN_PROMPT + f"\n\n{lang_instruction}\n"

    # Call 1: Generate all topics in one call
    gen_messages = [
        {"role": "system", "content": batch_gen_prompt},
        {"role": "user", "content": json.dumps(compact_input, ensure_ascii=False)},
    ]

    try:
        raw_gen = call_llm_chat(gen_messages)
        parsed_gen = parse_llm_json(raw_gen)
        generated_topics = parsed_gen.get("topics", {})
    except Exception as exc:
        logger.warning(f"Batch AI generation call failed: {exc}")
        notes.append(f"AI batch generation failed ({exc}); verified template used.")
        return {}, notes

    if not isinstance(generated_topics, dict) or not generated_topics:
        notes.append("AI generation returned empty topics map; verified template used.")
        return {}, notes

    # Call 2: Audit all generated topics in one call
    audit_messages = [
        {"role": "system", "content": BATCH_AUDIT_PROMPT},
        {"role": "user", "content": json.dumps({"generated": generated_topics}, ensure_ascii=False)},
    ]

    rejected_topics = set()
    try:
        raw_audit = call_llm_chat(audit_messages)
        parsed_audit = parse_llm_json(raw_audit)
        for rej in parsed_audit.get("rejected_topics", []):
            rejected_topics.add(str(rej).strip())
        if parsed_audit.get("notes"):
            notes.extend(parsed_audit["notes"])
    except Exception as exc:
        logger.warning(f"Batch AI audit call failed: {exc}")
        notes.append(f"AI audit call warning ({exc}); continuing with grounding gate.")

    final_results: Dict[str, Dict[str, Any]] = {}

    for topic, pkg in topics_packages.items():
        if topic in rejected_topics:
            notes.append(f"Topic '{topic}' rejected during AI compliance audit; fallback to template.")
            continue

        raw_topic_data = generated_topics.get(topic)
        if not raw_topic_data or not isinstance(raw_topic_data, dict):
            continue

        # Enforce limits
        allowed_ids = pkg["allowed_ids"]
        cleaned_topic = enforce_topic_json_limits(raw_topic_data, allowed_ids)
        final_results[topic] = cleaned_topic

    return final_results, notes
