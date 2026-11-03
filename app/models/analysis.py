from typing import Dict, Iterable, List, Optional, Tuple

from app import config


def flag_values(values: Dict[str, float], specs: Iterable) -> List[dict]:
    spec_map = {s.name: s for s in specs}
    rows = []
    for name, v in values.items():
        lo, hi = config.REFERENCE_RANGES.get(name, (None, None))
        s = spec_map.get(name)
        row = {"name": name, "marker": s.label if s else name, "unit": s.unit if s else "",
               "value": float(v), "range": (lo, hi), "status": "UNKNOWN",
               "pos": None, "zone_start": None, "zone_width": None}
        if lo is not None:
            row["status"] = "LOW" if v < lo else "HIGH" if v > hi else "NORMAL"
            ext = max(hi - lo, 1e-9)
            a_lo = min(max(lo - 0.5 * ext, 0.0), v)
            a_hi = max(hi + 0.5 * ext, v)
            span = max(a_hi - a_lo, 1e-9)
            row["pos"] = (v - a_lo) / span
            row["zone_start"] = (lo - a_lo) / span
            row["zone_width"] = (hi - lo) / span
        rows.append(row)
    return rows


def risk_band(p: float) -> Tuple[str, str]:
    for upper, label, cls in config.RISK_BANDS:
        if p < upper:
            return label, cls
    return config.RISK_BANDS[-1][1], config.RISK_BANDS[-1][2]


def findings(flags: List[dict]) -> List[str]:
    abnormal = [r for r in flags if r["status"] in ("LOW", "HIGH")]
    if not abnormal:
        return [f"All {len(flags)} biomarkers are within typical adult reference ranges."]
    verb = "falls" if len(abnormal) == 1 else "fall"
    out = [f"{len(abnormal)} of {len(flags)} biomarkers {verb} outside typical adult reference ranges."]
    for r in abnormal:
        lo, hi = r["range"]
        out.append(f"{r['marker']} is {r['status'].lower()} "
                   f"({r['value']:g} {r['unit']}; typical {lo:g} - {hi:g}).")
    return out


def consistency(is_positive: bool, probability: float, flags: List[dict]) -> Optional[Dict[str, str]]:
    """Flag a model output that contradicts the reference-range check, instead of hiding it."""
    n = len(flags)
    abnormal = sum(1 for r in flags if r["status"] in ("LOW", "HIGH"))
    if is_positive and abnormal == 0:
        return {"title": "Result does not match the lab values",
                "text": f"The model estimates {probability:.1%} probability of liver disease, but all {n} "
                        "biomarkers are inside typical adult ranges. The model can react strongly to small "
                        "changes in a single value, so treat this output as unreliable and have a clinician "
                        "interpret the panel."}
    if not is_positive and abnormal >= 3:
        return {"title": "Result does not match the lab values",
                "text": f"The model reports no liver disease, but {abnormal} of {n} biomarkers are outside "
                        "typical adult ranges. Do not read this as reassurance; have a clinician interpret "
                        "the panel."}
    return None
