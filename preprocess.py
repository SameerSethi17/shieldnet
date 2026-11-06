# preprocess.py -- ONE transformation used by training AND the website
import numpy as np
import pandas as pd


def normalise_text(df, text_cols, collapse):
    """Lower-case/strip text columns; rare values of collapsed columns become 'other'."""
    t = pd.DataFrame(index=df.index)
    for c in text_cols:
        s = df[c].astype(str).str.strip().str.lower()
        if c in collapse:
            s = s.where(s.isin(collapse[c]), "other")
        t[c] = s
    return t


def to_model_input(df, pre):
    """Raw feature table -> scaled float32 matrix in the EXACT training column order.
    Raises KeyError listing any required column that is missing."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    missing = [c for c in pre["raw_features"] if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns ({len(missing)}): {missing}")

    num = (df[pre["num_cols"]]
           .replace([np.inf, -np.inf], np.nan)
           .to_numpy(dtype=np.float64))
    parts = [pre["scaler"].transform(num).astype(np.float32)]
    if pre["text_cols"]:
        t = normalise_text(df, pre["text_cols"], pre["collapse"])
        parts.append(pre["encoder"].transform(t).astype(np.float32))
    return np.hstack(parts)