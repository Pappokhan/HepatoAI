import re
import time
from typing import Callable, Dict, List, Optional

import requests

from app import config


class LLMError(Exception):
    pass


GEMINI_FALLBACKS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash",
                    "gemini-flash-latest"]
GROQ_FALLBACKS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
_MODEL_CACHE: Dict[str, str] = {}


def _key(provider: str) -> Optional[str]:
    return config.local_setting("GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY") or None


def detect_provider() -> Optional[str]:
    forced = config.local_setting("LLM_PROVIDER").lower()
    if forced in ("gemini", "groq"):
        return forced
    for p in ("gemini", "groq"):
        if _key(p):
            return p
    return None


def rank_gemini(names: List[str]) -> List[str]:
    bad = ("image", "tts", "audio", "live", "embed", "aqa", "robotics", "computer", "imagen",
           "veo", "learnlm", "gemma", "vision")
    def score(n: str):
        low = n.lower()
        experimental = any(x in low for x in ("preview", "exp", "thinking"))
        tier = 1 if "lite" in low else 0 if "flash" in low else 2 if "pro" in low else 3
        m = re.search(r"gemini-(\d+(?:\.\d+)?)", low)
        version = 99.0 if "latest" in low else (float(m.group(1)) if m else 0.0)
        return (experimental, tier, -version, low)
    return sorted((n for n in names if n.lower().startswith("gemini") and not any(b in n.lower() for b in bad)),
                  key=score)


def rank_groq(ids: List[str]) -> List[str]:
    bad = ("whisper", "guard", "tts", "playai", "orpheus", "embed", "safeguard", "compound")
    ok = [i for i in ids if not any(b in i.lower() for b in bad)]
    pref = [m for m in GROQ_FALLBACKS if m in ok]
    return pref + sorted(i for i in ok if i not in pref)


def _post_with_retry(url: str, retries: int = 2, **kwargs) -> requests.Response:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, **kwargs)
            if r.status_code in (500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return r
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise last_exc


class LLMClient:
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = (provider or detect_provider() or "").lower()
        self.api_key = config.clean_setting(api_key or (_key(self.provider) if self.provider else None)) or None
        self.model_used: Optional[str] = None

    @property
    def ready(self) -> bool:
        return self.provider in ("gemini", "groq") and bool(self.api_key)

    def chat(self, system: str, messages: List[Dict[str, str]]) -> str:
        if not self.ready:
            raise LLMError("No API key configured. Paste it into local_settings.py "
                           "(GEMINI_API_KEY or GROQ_API_KEY) or set it as an environment variable.")
        bad = next(((i, ch) for i, ch in enumerate(self.api_key) if not (32 < ord(ch) < 127)), None)
        if bad:
            raise LLMError(
                f"Your API key contains a character that is not allowed (character #{bad[0] + 1}: '{bad[1]}'). "
                "API keys use only English letters, digits, '-' and '_'. Delete the key and paste it again "
                "from Google AI Studio / Groq console (only the key, no extra text).")
        try:
            if self.provider == "gemini":
                return self._gemini(system, messages)
            return self._groq(system, messages)
        except UnicodeError:
            raise LLMError("The API key or model name contains non-English characters. "
                           "Please re-copy it and paste only the key.")
        except requests.Timeout:
            raise LLMError("The AI service timed out after several tries. Check your internet/VPN/firewall "
                           "(Google AI Studio must be reachable), then try again.")
        except requests.RequestException as e:
            raise LLMError(f"Could not reach the AI service ({type(e).__name__}). Check your internet connection.")

    def test(self) -> str:
        self.chat("You are a connectivity test.", [{"role": "user", "content": "Reply with exactly: OK"}])
        return self.model_used or "?"

    def _initial_model(self) -> str:
        if self.provider == "gemini":
            return config.local_setting("GEMINI_MODEL") or _MODEL_CACHE.get("gemini") or config.GEMINI_MODEL_DEFAULT
        return config.local_setting("GROQ_MODEL") or _MODEL_CACHE.get("groq") or config.GROQ_MODEL_DEFAULT

    def _discover(self) -> List[str]:
        try:
            if self.provider == "gemini":
                r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                                 params={"pageSize": 200}, headers={"x-goog-api-key": self.api_key}, timeout=20)
                if not r.ok:
                    return []
                names = [m["name"].split("/", 1)[-1] for m in r.json().get("models", [])
                         if "generateContent" in m.get("supportedGenerationMethods", [])]
                return rank_gemini(names)
            r = requests.get("https://api.groq.com/openai/v1/models",
                             headers={"Authorization": f"Bearer {self.api_key}"}, timeout=20)
            if not r.ok:
                return []
            return rank_groq([m["id"] for m in r.json().get("data", [])])
        except (requests.RequestException, KeyError, ValueError, TypeError):
            return []

    def _run(self, call: Callable[[str], requests.Response]) -> requests.Response:
        model = self._initial_model()
        tried = [model]
        r = call(model)
        if r.status_code in (404, 503):  # unknown/retired model, or model overloaded -> try another one
            fallbacks = GEMINI_FALLBACKS if self.provider == "gemini" else GROQ_FALLBACKS
            for alt in self._discover()[:4] + fallbacks:
                if alt in tried:
                    continue
                tried.append(alt)
                r = call(alt)
                if r.status_code not in (404, 503):
                    model = alt
                    break
        self._check(r, tried)
        self.model_used = model
        _MODEL_CACHE[self.provider] = model
        return r

    def _gemini(self, system, messages) -> str:
        def call(model):
            gen_cfg = {"temperature": 0.3, "maxOutputTokens": 4096}
            if "2.5" in model or "latest" in model:
                gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
            def post(cfg):
                return _post_with_retry(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    json={"system_instruction": {"parts": [{"text": system}]},
                          "contents": [{"role": "user" if m["role"] == "user" else "model",
                                        "parts": [{"text": m["content"]}]} for m in messages],
                          "generationConfig": cfg},
                    headers={"x-goog-api-key": self.api_key}, timeout=config.LLM_TIMEOUT)
            r = post(gen_cfg)
            if r.status_code == 400 and "thinkingConfig" in gen_cfg:
                gen_cfg.pop("thinkingConfig")
                r = post(gen_cfg)
            return r
        r = self._run(call)
        try:
            parts = r.json()["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, TypeError, ValueError):
            text = ""
        if not text:
            raise LLMError("The AI service returned an empty or blocked response. Try rephrasing.")
        return text

    def _groq(self, system, messages) -> str:
        def call(model):
            return _post_with_retry(
                "https://api.groq.com/openai/v1/chat/completions",
                json={"model": model, "temperature": 0.3,
                      "messages": [{"role": "system", "content": system}] + messages},
                headers={"Authorization": f"Bearer {self.api_key}"}, timeout=config.LLM_TIMEOUT)
        r = self._run(call)
        try:
            text = r.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            text = ""
        if not text:
            raise LLMError("The AI service returned an empty response.")
        return text

    def _api_message(self, r) -> str:
        try:
            msg = r.json()["error"]["message"]
        except Exception:
            msg = ""
        msg = re.sub(r"\s+", " ", str(msg))
        if self.api_key:
            msg = msg.replace(self.api_key, "***")
        return msg[:200]

    def _check(self, r, tried: List[str]):
        if r.ok:
            return
        msg = self._api_message(r)
        code = r.status_code
        if code in (401, 403) or (code == 400 and "api key" in msg.lower()):
            raise LLMError("The API key was rejected. Please check it" + (f" ({msg})" if msg else "") + ".")
        if code == 429:
            raise LLMError("Rate limit or quota reached. Wait a moment and retry" + (f" ({msg})" if msg else "") + ".")
        if code == 404:
            var = "GEMINI_MODEL" if self.provider == "gemini" else "GROQ_MODEL"
            raise LLMError(f"No working model found (tried: {', '.join(tried)}). "
                           f"Set {var} in local_settings.py to a model available to your key.")
        raise LLMError(f"AI service error (HTTP {code})" + (f": {msg}" if msg else "."))
