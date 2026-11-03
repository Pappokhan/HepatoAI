from typing import Dict, List, Optional

from app import config
from app.models import LLMClient, LLMError, PredictionResult, consistency, detect_provider, flag_values

SYSTEM_RULES = """You are the friendly assistant inside HepatoAI, a liver-function screening app.
Rules:
- You explain results from a machine-learning model that uses 8 routine liver-panel markers. It is a statistical screening aid, NOT a diagnosis.
- Use plain, simple language. Reply in the same language the user writes in (English or Bangla).
- When 'Latest prediction' data is given below, the user has ALREADY entered it: never ask them to share their values, and use it in your answers (even for a greeting, mention you can see their latest result).
- Use the patient data below when it exists. If no prediction has been run, say so and answer in general terms.
- Never diagnose, prescribe, or give medication doses. For concerns or abnormal values, advise seeing a qualified doctor.
- Reference ranges are typical adult values and vary by lab; say so when relevant.
- If asked something unrelated to liver health or this app, politely steer back.
- Be concise and do not invent values that were not given."""


class AgentController:
    def __init__(self, feature_specs):
        self.specs = {s.name: s for s in feature_specs}

    def flag_values(self, values: Dict[str, float]) -> List[dict]:
        return flag_values(values, self.specs.values())

    def system_prompt(self, context: Optional[dict]) -> str:
        if not context:
            return SYSTEM_RULES + "\n\nCurrent data: no prediction has been run yet."
        res: PredictionResult = context["result"]
        lines = [
            f"- {r['marker']}: {r['value']:g} {r['unit']} "
            f"(typical {r['range'][0]:g}-{r['range'][1]:g}) -> {r['status']}"
            for r in self.flag_values(context["values"])
        ]
        flags = self.flag_values(context["values"])
        n_abnormal = sum(1 for r in flags if r["status"] in ("LOW", "HIGH"))
        mismatch = consistency(res.is_positive, res.probability_positive, flags)
        note = (f"\n- WARNING: {mismatch['text']} Tell the user about this mismatch plainly."
                if mismatch else "")
        return (SYSTEM_RULES + "\n\nLatest prediction:\n"
                f"- Model output: {res.label_text}\n"
                f"- Probability of liver disease: {res.probability_positive:.1%}\n"
                f"- Markers outside typical range: {n_abnormal} of {len(flags)}{note}\n"
                "Patient markers:\n" + "\n".join(lines))

    def provider_ready(self, provider: Optional[str] = None, api_key: Optional[str] = None) -> bool:
        return LLMClient(provider, api_key).ready

    def default_provider(self) -> Optional[str]:
        return detect_provider()

    def test_connection(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        client = LLMClient(provider, api_key)
        try:
            model = client.test()
            return True, f"Connected to {client.provider} (model: {model})."
        except LLMError as e:
            return False, str(e)

    def ask(self, history: List[Dict[str, str]], context: Optional[dict],
            provider: Optional[str] = None, api_key: Optional[str] = None) -> str:
        client = LLMClient(provider, api_key)
        recent = history[-config.MAX_HISTORY_MESSAGES:]
        while recent and recent[0]["role"] != "user":
            recent = recent[1:]
        return client.chat(self.system_prompt(context), recent)
