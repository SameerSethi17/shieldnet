# app/engine.py -- all prediction logic for the website (no Streamlit code, so it can be tested alone)
import io
import platform
from importlib import metadata

import numpy as np
import pandas as pd
import joblib

from preprocess import to_model_input

MAX_ROWS = 200_000


def load_bundle(path):
    return joblib.load(path)


def read_csv_bytes(raw):
    """Read an uploaded CSV. Tries UTF-8, then cp1252 (the CIC-IDS2017 files need it), then latin-1."""
    last = None
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc, low_memory=False), enc
        except UnicodeDecodeError as e:
            last = e
    raise ValueError(f"Could not decode the file: {last}")


def prepare(df, bundle):
    """Validate columns, coerce to numbers, flag unusable rows.
    Returns (features or None, info). features is None when required columns are missing."""
    pre = bundle["preprocessor"]
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    info = {"rows_uploaded": len(df), "duplicate_columns": [], "missing": [], "extra": [],
            "rows_used": 0, "rows_skipped": 0, "row_numbers": np.array([], dtype=int)}
    if df.columns.duplicated().any():
        info["duplicate_columns"] = sorted(set(df.columns[df.columns.duplicated()]))
        df = df.loc[:, ~df.columns.duplicated()]
    required = list(pre["raw_features"])
    info["missing"] = [c for c in required if c not in df.columns]
    info["extra"] = [c for c in df.columns if c not in required]
    if info["missing"]:
        return None, info
    if len(df) > MAX_ROWS:
        df = df.iloc[:MAX_ROWS]
        info["truncated_to"] = MAX_ROWS
    feat = df[required].copy()
    num = list(pre["num_cols"])
    for c in num:
        feat[c] = pd.to_numeric(feat[c], errors="coerce")
    feat[num] = feat[num].replace([np.inf, -np.inf], np.nan)
    bad = feat[num].isna().any(axis=1).to_numpy()   # same rule as training: such rows are not used
    info["rows_skipped"] = int(bad.sum())
    info["rows_used"] = int((~bad).sum())
    info["row_numbers"] = np.where(~bad)[0] + 1      # 1-based data-row numbers in the uploaded file
    return feat.loc[~bad].reset_index(drop=True), info


def model_input(feat, bundle):
    """Raw features -> SAME saved scaler/encoder -> SAME selected features in the SAME order."""
    return to_model_input(feat, bundle["preprocessor"])[:, bundle["selected_indices"]]


def predict_proba(X, bundle):
    p = np.asarray(bundle["model"].predict_proba(X), dtype=np.float64)
    return p / np.maximum(p.sum(axis=1, keepdims=True), 1e-12)


def results_table(proba, bundle, row_numbers):
    names = np.array(bundle["class_names"])
    k = proba.argmax(axis=1)
    return pd.DataFrame({
        "row_in_file": row_numbers,
        "predicted_class": names[k],
        "confidence": proba.max(axis=1).round(4),
        "attack_probability": (1.0 - proba[:, bundle["benign_index"]]).round(4),
        "verdict": np.where(k == bundle["benign_index"], "benign", "ATTACK"),
    })


def make_report(bundle, info, res, filename):
    n = len(res)
    n_att = int((res["verdict"] == "ATTACK").sum())
    counts = res["predicted_class"].value_counts()
    lines = ["# ShieldNet prediction report", "",
             f"- Model for dataset: {bundle['display_name']}",
             f"- Model: {bundle['model_name']}",
             f"- File: {filename}",
             f"- Rows in file: {info['rows_uploaded']:,}",
             f"- Rows used for prediction: {info['rows_used']:,}",
             f"- Rows skipped (missing, infinite or non-numeric values): {info['rows_skipped']:,}",
             f"- Flows flagged as attack: {n_att:,} ({n_att / max(n, 1) * 100:.2f}% of predicted rows)",
             "", "## Predicted class counts", "", "| class | rows | share |", "|---|---:|---:|"]
    for c, v in counts.items():
        lines.append(f"| {c} | {v:,} | {v / n * 100:.2f}% |")
    if info.get("extra"):
        shown = ", ".join(info["extra"][:10]) + (" ..." if len(info["extra"]) > 10 else "")
        lines += ["", f"Extra columns in the file were ignored: {shown}"]
    lines += ["", "## Notes",
              "- The saved scaler, encoder and feature order from training were applied to every row.",
              "- Confidence is the model's highest class probability, not a guarantee of correctness.",
              "- Educational project: trained on public lab datasets, not validated on live traffic.",
              f"- Library versions used to train: {bundle['library_versions']}"]
    return "\n".join(lines) + "\n"


def _installed(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return "not installed"


def version_report(bundle):
    lib = type(bundle["model"]).__module__.split(".")[0]          # 'sklearn', 'lightgbm' or 'xgboost'
    wanted = ["python", "numpy", "pandas", "scipy", "scikit-learn", "joblib"]
    if lib in ("lightgbm", "xgboost"):
        wanted.append(lib)
    rows = []
    for pkg in wanted:
        trained = str(bundle["library_versions"].get(pkg, "unknown"))
        now = platform.python_version() if pkg == "python" else _installed(pkg)
        same = trained.split(".")[:2] == now.split(".")[:2] if pkg == "python" else trained == now
        rows.append({"package": pkg, "trained_with": trained, "running_with": now, "match": same})
    return pd.DataFrame(rows)