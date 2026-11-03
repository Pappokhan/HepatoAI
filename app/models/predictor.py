from dataclasses import dataclass
from typing import Dict, List

import warnings

import numpy as np
import pandas as pd

from app import config
from .model_loader import Artifacts

warnings.filterwarnings("ignore", message="X does not have valid feature names")


@dataclass
class PredictionResult:
    label: object
    is_positive: bool
    label_text: str
    probability_positive: float
    probabilities: Dict[str, float]


class LiverPredictor:
    def __init__(self, artifacts: Artifacts):
        self.model = artifacts.model
        self.scaler = artifacts.scaler
        self.feature_names: List[str] = artifacts.feature_names
        self.classes = list(getattr(self.model, "classes_", [0, 1]))

    def _positive_index(self) -> int:
        if config.POSITIVE_LABEL in self.classes:
            return self.classes.index(config.POSITIVE_LABEL)
        return len(self.classes) - 1

    def _transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.feature_names].astype(float)
        return self.scaler.transform(X)

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        X = self._transform(df)
        proba = self.model.predict_proba(X)
        pos_idx = self._positive_index()
        pos_label = self.classes[pos_idx]
        pred = np.array(self.classes)[proba.argmax(axis=1)]

        out = df.copy()
        out["Prediction"] = np.where(pred == pos_label, config.POSITIVE_TEXT, config.NEGATIVE_TEXT)
        out["P(disease)"] = proba[:, pos_idx].round(4)
        return out

    def predict_one(self, values: Dict[str, float]) -> PredictionResult:
        df = pd.DataFrame([values])
        proba = self.model.predict_proba(self._transform(df))[0]
        pos_idx = self._positive_index()
        pred_idx = int(np.argmax(proba))
        is_pos = pred_idx == pos_idx
        return PredictionResult(
            label=self.classes[pred_idx],
            is_positive=is_pos,
            label_text=config.POSITIVE_TEXT if is_pos else config.NEGATIVE_TEXT,
            probability_positive=float(proba[pos_idx]),
            probabilities={str(c): float(p) for c, p in zip(self.classes, proba)},
        )
