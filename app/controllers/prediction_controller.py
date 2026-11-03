from datetime import datetime, timezone
from typing import Dict, List

import pandas as pd

from app import config
from app.models import (LiverPredictor, PredictionResult, build_report_pdf, consistency, findings,
                        flag_values, load_artifacts, make_report_id, risk_band)


class PredictionController:
    def __init__(self):
        self.artifacts = load_artifacts()
        self.predictor = LiverPredictor(self.artifacts)

    @property
    def feature_specs(self) -> List[config.FeatureSpec]:
        return config.FEATURE_SPECS

    @property
    def feature_names(self) -> List[str]:
        return self.artifacts.feature_names

    @property
    def feature_groups(self):
        return config.FEATURE_GROUPS

    def model_summary(self) -> Dict:
        info = self.artifacts.info
        return {
            "name": info.get("best_model_name", type(self.artifacts.model).__name__),
            "accuracy": info.get("best_accuracy"),
            "n_features": info.get("n_features", len(self.feature_names)),
            "all_models": info.get("all_models_accuracy", {}),
        }

    def template_csv(self) -> str:
        defaults = {s.name: s.default for s in self.feature_specs}
        return pd.DataFrame([defaults])[self.feature_names].to_csv(index=False)

    def predict_single(self, values: Dict[str, float]) -> PredictionResult:
        return self.predictor.predict_one(values)

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in self.feature_names if c not in df.columns]
        if missing:
            raise ValueError("Missing required column(s): " + ", ".join(missing))
        data = df[self.feature_names].apply(pd.to_numeric, errors="coerce")
        bad = data.isna().any(axis=1)
        if bad.any():
            rows = ", ".join(str(i + 2) for i in data.index[bad][:10])
            raise ValueError(f"Non-numeric or empty values found (CSV line(s): {rows}).")
        return self.predictor.predict_dataframe(data)

    def run_prediction(self, values: Dict[str, float], patient: Dict[str, str]) -> dict:
        ts = datetime.now(timezone.utc)
        return {"values": values, "patient": patient, "timestamp": ts,
                "result": self.predict_single(values),
                "report_id": make_report_id(ts, values)}

    def analyze(self, pred: dict) -> dict:
        flags = flag_values(pred["values"], self.feature_specs)
        res = pred["result"]
        return {"flags": flags, "findings": findings(flags),
                "band": risk_band(res.probability_positive),
                "notice": consistency(res.is_positive, res.probability_positive, flags)}

    def report_filename(self, pred: dict) -> str:
        return f"HepatoAI_report_{pred['report_id']}.pdf"

    def build_report(self, pred: dict, analysis: dict) -> bytes:
        return build_report_pdf(
            values=pred["values"], result=pred["result"], flags=analysis["flags"],
            findings=analysis["findings"], band=analysis["band"], notice=analysis.get("notice"),
            patient=pred["patient"],
            model_summary=self.model_summary(), timestamp=pred["timestamp"],
            report_id=pred["report_id"], feature_labels=[s.label for s in self.feature_specs])
