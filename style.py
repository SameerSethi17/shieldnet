# app/style.py -- colourful look, hover effects, hero banner and feature cards for the ShieldNet website
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
html, body, .stApp, [data-testid="stMarkdownContainer"], button, input, textarea {
  font-family: 'Poppins', 'Segoe UI', Roboto, Arial, sans-serif;
}
.stApp {
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 0, 128, 0.30), transparent 38%),
    radial-gradient(circle at 88% 12%, rgba(0, 200, 255, 0.26), transparent 38%),
    radial-gradient(circle at 70% 90%, rgba(255, 190, 60, 0.16), transparent 36%),
    linear-gradient(-45deg, #0f0c29, #302b63, #1b2a6b, #4a1d6b, #0b3b5c, #24243e);
  background-size: 100% 100%, 100% 100%, 100% 100%, 400% 400%;
  background-attachment: fixed;
  animation: snShift 22s ease infinite;
}
@keyframes snShift {
  0% { background-position: 0% 0%, 0% 0%, 0% 0%, 0% 50%; }
  50% { background-position: 0% 0%, 0% 0%, 0% 0%, 100% 50%; }
  100% { background-position: 0% 0%, 0% 0%, 0% 0%, 0% 50%; }
}
@keyframes snFadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(22, 16, 64, 0.94), rgba(46, 10, 74, 0.94));
  border-right: 1px solid rgba(255, 255, 255, 0.10);
}
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: 8px 12px; border-radius: 12px; transition: background .2s ease, transform .2s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: rgba(255, 255, 255, 0.13); transform: translateX(6px);
}
h2, h3 { color: #ffffff; letter-spacing: 0.2px; }
[data-testid="stMetric"] {
  background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 18px; padding: 16px 18px; backdrop-filter: blur(10px);
  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-6px) scale(1.02); border-color: rgba(0, 229, 255, 0.65);
  box-shadow: 0 14px 32px rgba(0, 229, 255, 0.25);
}
[data-testid="stMetricValue"] { color: #7df9ff; font-weight: 800; text-shadow: 0 0 18px rgba(125, 249, 255, 0.35); }
[data-testid="stMetricLabel"] { opacity: 0.85; }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
  border: none; border-radius: 999px; padding: 0.6rem 1.5rem;
  background: linear-gradient(90deg, #7b2ff7, #f107a3);
  transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
}
[data-testid="stButton"] button p, [data-testid="stDownloadButton"] button p { color: #ffffff; font-weight: 600; }
[data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover {
  transform: translateY(-3px) scale(1.04); box-shadow: 0 10px 26px rgba(241, 7, 163, 0.45); filter: brightness(1.08);
}
[data-testid="stButton"] button:active, [data-testid="stDownloadButton"] button:active { transform: scale(0.98); }
button[data-baseweb="tab"] { border-radius: 12px 12px 0 0; transition: background .2s ease, transform .2s ease; }
button[data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.10); transform: translateY(-2px); }
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 14px;
  transition: border-color .25s ease, box-shadow .25s ease;
}
[data-testid="stExpander"]:hover { border-color: rgba(255, 78, 205, 0.7); box-shadow: 0 0 22px rgba(255, 78, 205, 0.22); }
[data-testid="stDataFrame"] {
  border-radius: 14px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.16); transition: box-shadow .25s ease;
}
[data-testid="stDataFrame"]:hover { box-shadow: 0 0 26px rgba(0, 229, 255, 0.25); }
[data-testid="stImage"] img { border-radius: 14px; box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35); transition: transform .25s ease; }
[data-testid="stImage"] img:hover { transform: scale(1.01); }
[data-testid="stAlert"] { border-radius: 14px; backdrop-filter: blur(6px); }
[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed rgba(0, 229, 255, 0.55); border-radius: 16px; background: rgba(255, 255, 255, 0.05);
  transition: background .2s ease, border-color .2s ease, transform .2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover { background: rgba(0, 229, 255, 0.10); border-color: #ff4ecd; transform: translateY(-2px); }
.sn-hero {
  padding: 26px 32px; margin-bottom: 18px; border-radius: 24px; backdrop-filter: blur(12px);
  background: linear-gradient(135deg, rgba(123, 47, 247, 0.38), rgba(0, 229, 255, 0.18));
  border: 1px solid rgba(255, 255, 255, 0.20); animation: snFadeUp .8s ease both;
}
.sn-badge { display: inline-block; font-size: .72rem; font-weight: 700; letter-spacing: 2px; color: #ffd166; margin-bottom: 4px; }
.sn-title {
  font-size: 3.1rem; font-weight: 800; line-height: 1.1; margin: 0 0 6px 0;
  background: linear-gradient(90deg, #00e5ff, #ff4ecd, #ffd166); -webkit-background-clip: text;
  background-clip: text; -webkit-text-fill-color: transparent; color: #00e5ff;
}
.sn-sub { font-size: 1.02rem; opacity: .92; margin: 0 0 14px 0; max-width: 780px; }
.sn-pill {
  display: inline-block; padding: 6px 14px; margin: 0 8px 6px 0; border-radius: 999px; font-size: .85rem;
  background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.26);
  transition: transform .2s ease, background .2s ease;
}
.sn-pill:hover { transform: translateY(-3px); background: rgba(255, 255, 255, 0.24); }
.sn-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; margin: 8px 0 22px 0; }
.sn-card {
  padding: 20px 20px 18px 20px; border-radius: 20px; background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.16); backdrop-filter: blur(10px); animation: snFadeUp .9s ease both;
  transition: transform .28s ease, box-shadow .28s ease, border-color .28s ease;
}
.sn-card:hover { transform: translateY(-8px); border-color: rgba(255, 78, 205, 0.75); box-shadow: 0 16px 38px rgba(123, 47, 247, 0.45); }
.sn-ico { font-size: 1.9rem; }
.sn-card h4 { margin: 8px 0 6px 0; font-size: 1.1rem; color: #7df9ff; }
.sn-card p { margin: 0; font-size: .92rem; opacity: .9; }
"""


def inject():
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


def hero(dataset_name, model_name):
    html = ("<div class='sn-hero'>"
            "<div class='sn-badge'>NETWORK INTRUSION DETECTION</div>"
            "<div class='sn-title'>ShieldNet</div>"
            "<p class='sn-sub'>Spot attack types in network traffic with machine learning, "
            "trained and tested on two public datasets.</p>"
            f"<span class='sn-pill'>Dataset: {dataset_name}</span>"
            f"<span class='sn-pill'>Model: {model_name}</span>"
            "<span class='sn-pill'>Evaluated on unseen test data</span>"
            "</div>")
    st.markdown(html, unsafe_allow_html=True)


def feature_cards():
    cards = [("📤", "Upload &amp; predict", "Drop in a CSV of network flows and get a class, a confidence and a downloadable report."),
             ("🎯", "Live demo", "Draw a real flow the model has never seen and watch it decide."),
             ("📊", "Results", "Browse every table and figure from the study, from data cleaning to SHAP.")]
    body = "".join(f"<div class='sn-card'><div class='sn-ico'>{i}</div><h4>{t}</h4><p>{d}</p></div>" for i, t, d in cards)
    st.markdown(f"<div class='sn-cards'>{body}</div>", unsafe_allow_html=True)