import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from app import config


@dataclass
class Artifacts:
    model: Any
    scaler: Any
    feature_names: List[str]
    info: Dict[str, Any]
    model_path: Path


def load_artifacts(artifacts_dir: Optional[Path] = None) -> Artifacts:
    d = Path(artifacts_dir) if artifacts_dir else config.ARTIFACTS_DIR

    model_path = next((d / f for f in config.MODEL_CANDIDATES if (d / f).exists()), None)
    if model_path is None:
        raise FileNotFoundError(f"No model file found in {d}. Expected one of {config.MODEL_CANDIDATES}")

    scaler = joblib.load(d / config.SCALER_FILE)
    model = joblib.load(model_path)
    feature_names = json.loads((d / config.FEATURES_FILE).read_text(encoding="utf-8"))

    info_path = d / config.MODEL_INFO_FILE
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}

    scaler_cols = getattr(scaler, "feature_names_in_", None)
    if scaler_cols is not None and list(scaler_cols) != list(feature_names):
        raise ValueError("feature_names.json does not match the scaler's feature order.")

    return Artifacts(model=model, scaler=scaler, feature_names=feature_names,
                     info=info, model_path=model_path)
