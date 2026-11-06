# app/app.py -- ShieldNet website.  Run from the project root:  streamlit run app/app.py
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import engine
import style

APP = Path(__file__).resolve().parent
DATASETS = {"UNSW-NB15": "unsw_nb15", "CIC-IDS2017": "cicids2017"}
st.set_page_config(page_title="ShieldNet", page_icon="🛡️", layout="wide")
style.inject()

@st.cache_resource(show_spinner="Loading model ...")
def get_bundle(key):
    return engine.load_bundle(APP / "bundles" / f"{key}_bundle.joblib")


@st.cache_data(show_spinner=False)
def get_demo(key):
    return pd.read_parquet(APP / "demo" / f"{key}_demo.parquet")


@st.cache_data(show_spinner=False)
def get_manifest():
    return json.loads((APP / "manifest.json").read_text(encoding="utf-8"))


def prob_chart(proba, names, top=5):
    order = np.argsort(-proba)[:top][::-1]
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(order) + 1.3))
    bars = ax.barh([names[i] for i in order], proba[order], color="#3b6ea8")
    ax.bar_label(bars, labels=[f"{proba[i] * 100:.1f}%" for i in order], padding=3, fontsize=8)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Predicted probability")
    ax.set_title(f"Top {len(order)} class probabilities")
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ Overview
def page_overview(bundle, key):
    style.feature_cards()
    st.write(f"Multi-class detection of attack types on **{bundle['display_name']}**. "
             f"Final model: **{bundle['model_name']}**, chosen by validation macro-F1.")
    m = bundle["test_metrics"]
    c = st.columns(4)
    c[0].metric("Test accuracy", f"{m['accuracy']:.4f}")
    c[1].metric("Test macro-F1 (headline)", f"{m['f1_macro']:.4f}")
    c[2].metric("Test log loss", f"{m['log_loss']:.4f}")
    c[3].metric("Benign flows flagged as attack", f"{m['bin_fpr'] * 100:.2f}%")
    st.caption("All numbers on this page are read from the saved model bundle and results tables, "
               "measured on a held-out test split the model never saw.")

    tbl = pd.read_csv(APP / "results" / "tables" / "dataset_summary_clean.csv")
    row = tbl[tbl["dataset"] == bundle["display_name"]]
    if len(row):
        st.subheader("Dataset after cleaning")
        st.dataframe(row.set_index("dataset").T.reset_index(names="item").astype(str),
                     use_container_width=True, hide_index=True)

    st.subheader("What happens to an uploaded flow")
    st.markdown(
        "1. The columns are checked against the exact list used in training; missing columns stop the prediction.\n"
        "2. Rows with missing, infinite or non-numeric values are skipped, as in training.\n"
        "3. The **saved scaler** (and the saved one-hot encoder for UNSW-NB15) transform the numbers.\n"
        f"4. The same {len(bundle['selected_features'])} selected features, in the same order, go to the model.\n"
        "5. The model returns a probability for every class; the largest is the prediction and its "
        "probability is the confidence.")

    with st.expander("Classes the model can predict"):
        st.write(", ".join(bundle["class_names"]))
    with st.expander("Selected features, in the order the model uses them"):
        st.write(", ".join(bundle["selected_features"]))
    with st.expander("Environment check (library versions: trained vs running)"):
        vr = engine.version_report(bundle)
        if vr["match"].all():
            st.success("The running environment matches the one the model was trained in.")
        else:
            st.warning("Some versions differ from training. Predictions may warn or change; "
                       "use the pinned requirements.")
        st.dataframe(vr, use_container_width=True, hide_index=True)

    st.subheader("Limitations")
    st.markdown(
        "- Trained and tested on public lab datasets; this is not proof of performance on live traffic.\n"
        "- Large classes were capped in CIC-IDS2017, so its benign share is lower than in real traffic.\n"
        "- Some UNSW-NB15 rows have identical features but different labels, so some confusion is unavoidable.\n"
        "- The train/validation/test split is random by flow, so similar flows from one attack session "
        "can fall on both sides of a split.\n"
        "- The two datasets have different class sets; they are evaluated separately, with no cross-dataset claim.\n"
        "- Explanations (SHAP) show what the model uses, not what causes an attack.")
    if key == "cicids2017":
        st.markdown("- For CIC-IDS2017 the model relies strongly on *Destination Port* (SHAP rank 1), "
                    "which may partly reflect how the lab traffic was generated.")


# ------------------------------------------------------------------ Upload & predict
def page_upload(bundle, key):
    st.header("Upload a CSV of network flows")
    st.write("The file needs the **raw** feature columns of this dataset (no scaling beforehand). "
             "Extra columns such as the label are ignored. Sample files are in `app/sample_uploads/`.")
    with st.expander("Required columns"):
        st.code(", ".join(bundle["raw_features"]))
    up = st.file_uploader("CSV file", type=["csv"], key=f"upload_{key}")
    if up is None:
        return
    try:
        df, enc = engine.read_csv_bytes(up.getvalue())
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return
    feat, info = engine.prepare(df, bundle)
    st.write(f"Read **{info['rows_uploaded']:,}** rows and **{df.shape[1]}** columns (encoding: {enc}).")
    if info["duplicate_columns"]:
        st.warning(f"Duplicate column names, first copy used: {info['duplicate_columns']}")
    if info["missing"]:
        st.error(f"{len(info['missing'])} required column(s) are missing, so NO predictions were made. "
                 "Predicting without them would give silently wrong answers.")
        st.write("Missing columns:")
        st.code(", ".join(info["missing"]))
        return
    if info["extra"]:
        st.caption(f"Extra columns ignored: {', '.join(info['extra'][:8])}"
                   + (" ..." if len(info["extra"]) > 8 else ""))
    if info.get("truncated_to"):
        st.warning(f"Only the first {info['truncated_to']:,} rows were used.")
    if info["rows_skipped"]:
        st.warning(f"{info['rows_skipped']:,} row(s) were skipped because they contain missing, infinite "
                   "or non-numeric values (the same rule used in training).")
    if info["rows_used"] == 0:
        st.error("No usable rows left to predict.")
        return

    with st.spinner("Scaling and predicting ..."):
        proba = engine.predict_proba(engine.model_input(feat, bundle), bundle)
    res = engine.results_table(proba, bundle, info["row_numbers"])
    n = len(res)
    n_att = int((res["verdict"] == "ATTACK").sum())
    c = st.columns(3)
    c[0].metric("Flows predicted", f"{n:,}")
    c[1].metric("Flagged as attack", f"{n_att:,}")
    c[2].metric("Share flagged", f"{n_att / n * 100:.2f}%")

    counts = res["predicted_class"].value_counts().reindex(bundle["class_names"]).fillna(0).astype(int)
    counts = counts[counts > 0].sort_values()
    fig, ax = plt.subplots(figsize=(8, 0.45 * max(len(counts), 3) + 1.5))
    colors = ["#2e8b57" if cl == bundle["benign_label"] else "#b03a2e" for cl in counts.index]
    bars = ax.barh(list(counts.index), counts.values, color=colors)
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=3, fontsize=8)
    ax.set_xlim(right=counts.max() * 1.15)
    ax.set_xlabel("Number of flows")
    ax.set_title("Predicted class distribution (green = benign, red = attack)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    only_att = st.checkbox("Show only flows flagged as attack")
    shown = res[res["verdict"] == "ATTACK"] if only_att else res
    st.dataframe(shown.head(1000), use_container_width=True, hide_index=True)
    if len(shown) > 1000:
        st.caption(f"Showing the first 1,000 of {len(shown):,} rows. The download has all of them.")
    st.download_button("Download predictions (CSV)", res.to_csv(index=False).encode("utf-8"),
                       file_name=f"shieldnet_predictions_{key}.csv", mime="text/csv")
    report = engine.make_report(bundle, info, res, up.name)
    st.download_button("Download summary report (Markdown)", report.encode("utf-8"),
                       file_name=f"shieldnet_report_{key}.md", mime="text/markdown")


# ------------------------------------------------------------------ Demo
def page_demo(bundle, key):
    st.header("Demo: classify a real flow from the held-out test set")
    demo = get_demo(key)
    classes = [c for c in bundle["class_names"] if c in set(demo["true_label"])]
    true_cls = st.selectbox("Traffic type to draw", classes)
    state_key = f"demo_{key}"
    if st.button("Pick a random real flow of this type", type="primary"):
        pool = demo.index[demo["true_label"] == true_cls].to_list()
        st.session_state[state_key] = (true_cls, random.choice(pool))
    chosen = st.session_state.get(state_key)
    if not chosen:
        st.info("Click the button to draw a real flow. The model has never seen it during training.")
        return
    chosen_cls, idx = chosen
    row = demo.loc[[idx]]
    feat, info = engine.prepare(row, bundle)
    if feat is None or len(feat) == 0:
        st.error("This row could not be used.")
        return
    X = engine.model_input(feat, bundle)
    proba = engine.predict_proba(X, bundle)[0]
    names = bundle["class_names"]
    pred = int(np.argmax(proba))
    c = st.columns(3)
    c[0].metric("True class", chosen_cls)
    c[1].metric("Predicted class", names[pred])
    c[2].metric("Confidence", f"{proba[pred] * 100:.1f}%")
    if names[pred] == chosen_cls:
        st.success("Correct: the prediction matches the true class.")
    else:
        st.error("Wrong: the prediction differs from the true class. The model is not perfect.")
    fig = prob_chart(proba, names)
    st.pyplot(fig)
    plt.close(fig)
    with st.expander("Feature values of this flow (the ones the model uses)"):
        vals = []
        for j, f in enumerate(bundle["selected_features"]):
            if f in row.columns:
                v = row.iloc[0][f]
                shown = f"{float(v):.6g}" if isinstance(v, (int, float, np.number)) else str(v)
            else:
                shown = f"{int(round(float(X[0, j])))} (one-hot flag)"
            vals.append({"feature": f, "value": shown})
        st.dataframe(pd.DataFrame(vals), use_container_width=True, hide_index=True)


# ------------------------------------------------------------------ Results
def page_results(bundle, key):
    st.header("Saved results")
    manifest = get_manifest()
    tab_t, tab_f = st.tabs(["Tables", "Figures"])
    with tab_t:
        items = [m for m in manifest if m["kind"] == "table" and m["dataset"] in ("all", key)]
        if not items:
            st.info("No tables found.")
        else:
            label = st.selectbox("Table", [m["title"] for m in items])
            item = next(m for m in items if m["title"] == label)
            df = pd.read_csv(APP / "results" / item["file"])
            if "dataset" in df.columns:
                df = df[df["dataset"] == bundle["display_name"]]
            if df.empty:
                st.info("This table has no rows (nothing to report).")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Source: {item['file']}")
    with tab_f:
        items = [m for m in manifest if m["kind"] == "figure" and m["dataset"] in ("all", key)]
        if not items:
            st.info("No figures found.")
        else:
            label = st.selectbox("Figure", [m["title"] for m in items])
            item = next(m for m in items if m["title"] == label)
            st.image(str(APP / "results" / item["file"]), caption=item["title"])


# ------------------------------------------------------------------ main
st.sidebar.title("ShieldNet")
ds_name = st.sidebar.selectbox("Dataset / model", list(DATASETS))
key = DATASETS[ds_name]
bundle = get_bundle(key)
page = st.sidebar.radio("Page", ["Overview", "Upload & predict", "Demo", "Results"])
st.sidebar.caption(f"Model: {bundle['model_name']}")
st.sidebar.caption("Educational project, not a production security tool.")
style.hero(ds_name, bundle["model_name"])
if page == "Overview":
    page_overview(bundle, key)
elif page == "Upload & predict":
    page_upload(bundle, key)
elif page == "Demo":
    page_demo(bundle, key)
else:
    page_results(bundle, key)