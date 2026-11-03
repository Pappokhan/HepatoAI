import importlib
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

MODEL_CANDIDATES = ["best_model.pkl", "LightGBM_best_model.pkl"]
SCALER_FILE = "scaler.pkl"
FEATURES_FILE = "feature_names.json"
MODEL_INFO_FILE = "model_info.json"

APP_TITLE = "HepatoAI"
APP_ICON = "🩺"

POSITIVE_LABEL = 1
POSITIVE_TEXT = "Liver disease indicated"
NEGATIVE_TEXT = "No liver disease indicated"


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    label: str
    unit: str
    min_value: float
    max_value: float
    default: float
    step: float
    help: str
    short: str = ""
    fmt: str = "%.2f"

    @property
    def input_label(self) -> str:
        base = self.short or self.label
        return base if self.unit == "ratio" else f"{base} ({self.unit})"


FEATURE_SPECS = [
    FeatureSpec("Alkphos Alkaline Phosphotase", "Alkaline Phosphatase (ALP)", "U/L",
                10.0, 3000.0, 100.0, 1.0, "Alkaline phosphatase: an enzyme found in the liver and bile ducts.",
                short="ALP", fmt="%.0f"),
    FeatureSpec("Sgot Aspartate Aminotransferase", "SGOT / AST", "U/L",
                1.0, 5000.0, 30.0, 1.0, "SGOT / AST: aspartate aminotransferase.",
                short="SGOT / AST", fmt="%.0f"),
    FeatureSpec("Sgpt Alamine Aminotransferase", "SGPT / ALT", "U/L",
                1.0, 3000.0, 30.0, 1.0, "SGPT / ALT: alanine aminotransferase.",
                short="SGPT / ALT", fmt="%.0f"),
    FeatureSpec("Total Bilirubin", "Total Bilirubin", "mg/dL",
                0.1, 80.0, 0.8, 0.1, "Total bilirubin in blood.",
                short="Total bilirubin", fmt="%.1f"),
    FeatureSpec("A/G Ratio Albumin and Globulin Ratio", "Albumin/Globulin Ratio", "ratio",
                0.1, 3.0, 1.2, 0.05, "Albumin to globulin (A/G) ratio.",
                short="A/G ratio", fmt="%.2f"),
    FeatureSpec("Direct Bilirubin", "Direct Bilirubin", "mg/dL",
                0.0, 25.0, 0.2, 0.1, "Conjugated (direct) bilirubin.",
                short="Direct bilirubin", fmt="%.1f"),
    FeatureSpec("ALB Albumin", "Albumin", "g/dL",
                0.5, 6.0, 4.0, 0.1, "Albumin: the main protein made by the liver.",
                short="Albumin", fmt="%.1f"),
    FeatureSpec("Total Protiens", "Total Proteins", "g/dL",
                2.0, 10.0, 7.0, 0.1, "Total protein in blood.",
                short="Total protein", fmt="%.1f"),
]


GEMINI_MODEL_DEFAULT = "gemini-3.1-flash-lite"
GROQ_MODEL_DEFAULT = "llama-3.3-70b-versatile"
LLM_TIMEOUT_SECONDS = 60
LLM_TIMEOUT = (10, 90)
MAX_HISTORY_MESSAGES = 12

REFERENCE_RANGES = {
    "Alkphos Alkaline Phosphotase": (44.0, 147.0),
    "Sgot Aspartate Aminotransferase": (10.0, 40.0),
    "Sgpt Alamine Aminotransferase": (7.0, 56.0),
    "Total Bilirubin": (0.1, 1.2),
    "A/G Ratio Albumin and Globulin Ratio": (1.1, 2.5),
    "Direct Bilirubin": (0.0, 0.3),
    "ALB Albumin": (3.5, 5.0),
    "Total Protiens": (6.0, 8.3),
}

QUICK_PROMPTS = [
    "Explain my result in simple words",
    "Which markers are outside the normal range?",
    "What should I ask my doctor?",
]


APP_SUBTITLE = "AI-assisted liver function screening from 8 routine blood markers"

RISK_BANDS = [
    (0.35, "Low", "ok"),
    (0.65, "Borderline", "warn"),
    (1.01, "High", "bad"),
]

FEATURE_GROUPS = [
    ("Liver enzymes", ["Alkphos Alkaline Phosphotase",
                       "Sgot Aspartate Aminotransferase",
                       "Sgpt Alamine Aminotransferase"]),
    ("Bilirubin", ["Total Bilirubin", "Direct Bilirubin"]),
    ("Proteins", ["ALB Albumin", "Total Protiens",
                  "A/G Ratio Albumin and Globulin Ratio"]),
]

DISCLAIMER = ("This tool is for research and educational use only. It is not a medical "
              "diagnosis. Please consult a qualified clinician for any health decision.")


_INVISIBLE = {ord(c): None for c in "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00a0"}
_QUOTES = "\"'`\u201c\u201d\u2018\u2019\u00ab\u00bb"


def clean_setting(raw) -> str:
    text = str(raw or "").translate(_INVISIBLE).strip()
    return text.strip(_QUOTES).strip()


def local_setting(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if not val:
        try:
            val = getattr(importlib.import_module("local_settings"), name, "")
        except Exception:
            val = ""
    return clean_setting(val) or default
