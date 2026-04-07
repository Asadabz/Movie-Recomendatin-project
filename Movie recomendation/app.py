import streamlit as st
import pickle
import pandas as pd
import random
import requests
import base64
from io import BytesIO

# ---------------- LOAD DATA ----------------
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

st.set_page_config(page_title="CineMatch", page_icon="🎬", layout="wide")

OMDB_KEY = "7ead3d81"

# ---------------- FETCH POSTER AS BASE64 (OMDb) ----------------
@st.cache_data(show_spinner=False)
def fetch_poster_b64(title):
    try:
        # Step 1: search by title to get imdbID
        search_url = f"https://www.omdbapi.com/?s={requests.utils.quote(title)}&type=movie&apikey={OMDB_KEY}"
        r = requests.get(search_url, timeout=6)
        data = r.json()
        results = data.get("Search", [])
        if not results:
            # fallback: direct title lookup
            r = requests.get(f"https://www.omdbapi.com/?t={requests.utils.quote(title)}&type=movie&apikey={OMDB_KEY}", timeout=6)
            data = r.json()
            poster_url = data.get("Poster", "")
        else:
            # Step 2: fetch full details using imdbID for accurate poster
            imdb_id = results[0].get("imdbID", "")
            r2 = requests.get(f"https://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_KEY}", timeout=6)
            poster_url = r2.json().get("Poster", "")

        if poster_url and poster_url != "N/A":
            img_r = requests.get(poster_url, timeout=8)
            if img_r.status_code == 200:
                b64 = base64.b64encode(img_r.content).decode()
                return f"data:image/jpeg;base64,{b64}"
    except:
        pass
    return None

# ---------------- RECOMMEND ----------------
def recommend(movie_name):
    match = movies[movies['title'].str.lower() == movie_name.lower()]
    if match.empty:
        return [], []
    idx = match.index[0]
    distances = similarity[idx]
    top = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:51]
    titles = [movies.iloc[i[0]].title for i in top]
    posters = [fetch_poster_b64(t) for t in titles]
    return titles, posters

# ---------------- WALL POSTERS ----------------
all_titles = movies['title'].dropna().tolist()
random.seed(42)
wall_titles = random.sample(all_titles, min(32, len(all_titles)))

@st.cache_data(show_spinner=False)
def get_wall_posters(titles):
    out = []
    for t in titles:
        try:
            search_url = f"https://www.omdbapi.com/?s={requests.utils.quote(t)}&type=movie&apikey={OMDB_KEY}"
            r = requests.get(search_url, timeout=5)
            results = r.json().get("Search", [])
            if results and results[0].get("Poster") and results[0]["Poster"] != "N/A":
                out.append((t, results[0]["Poster"]))
            else:
                r2 = requests.get(f"https://www.omdbapi.com/?t={requests.utils.quote(t)}&type=movie&apikey={OMDB_KEY}", timeout=5)
                poster = r2.json().get("Poster", "")
                out.append((t, poster if poster and poster != "N/A" else None))
        except:
            out.append((t, None))
    return out

# =================== CSS ===================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@1,700&display=swap');

html, body, .stApp { background: #04060f !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important; padding-bottom: 0 !important;
    padding-left: 0 !important; padding-right: 0 !important;
    max-width: 100% !important;
}

/* POSTER WALL */
.pwall {
    position: fixed; inset: 0;
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    grid-auto-rows: 180px;
    gap: 4px; padding: 4px;
    z-index: 0; overflow: hidden;
    transform: skewY(-4deg) scale(1.14);
    transform-origin: center;
    pointer-events: none;
}
.wposter {
    border-radius: 6px; overflow: hidden;
    background: #111827;
    animation: fadeUp 1s ease both;
}
.wposter img {
    width: 100%; height: 100%;
    object-fit: cover; display: block;
    opacity: 0.55;
}
.wposter-blank {
    width: 100%; height: 100%;
    background: linear-gradient(155deg, #1a1a2e, #0f3460);
    opacity: 0.3;
}
@keyframes fadeUp { from { opacity:0; transform:translateY(18px); } to { opacity:1; transform:translateY(0); } }

/* VIGNETTE */
.vignette {
    position: fixed; inset: 0; z-index: 1; pointer-events: none;
    background:
        radial-gradient(ellipse 65% 55% at 50% 50%, rgba(4,6,15,0.72) 20%, transparent 100%),
        linear-gradient(180deg, rgba(4,6,15,0.88) 0%, rgba(4,6,15,0.45) 35%, rgba(4,6,15,0.45) 65%, rgba(4,6,15,0.88) 100%);
}

/* HERO */
.hero-wrap {
    position: relative; z-index: 10;
    text-align: center; padding: 48px 20px 28px;
}
.eyebrow {
    font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 700;
    letter-spacing: .45em; color: #f59e0b; text-transform: uppercase;
    display: inline-flex; align-items: center; gap: 10px; margin-bottom: 14px;
}
.eyebrow::before, .eyebrow::after { content:''; width:28px; height:1px; background:#f59e0b; opacity:.5; display:block; }
.htitle {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(52px, 8vw, 96px);
    color: #fff; letter-spacing: .04em; line-height: .92; margin-bottom: 10px;
}
.htitle em { font-family:'Playfair Display',serif; font-style:italic; color:#f59e0b; }
.hsub {
    font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 300;
    color: rgba(255,255,255,0.28); letter-spacing: .2em; text-transform: uppercase;
}

/* INPUT */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important; color: #fff !important;
    font-family: 'Inter', sans-serif !important; font-size: 15px !important;
    padding: 14px 16px !important; caret-color: #f59e0b !important;
}
.stTextInput > div > div > input:focus {
    border-color: #f59e0b !important;
    box-shadow: 0 0 0 3px rgba(245,158,11,0.2) !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(255,255,255,0.25) !important; }
.stTextInput label, .stSelectbox label {
    color: rgba(255,255,255,0.35) !important; font-family:'Inter',sans-serif !important;
    font-size: 10px !important; letter-spacing:.3em !important; text-transform:uppercase !important;
}
div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important; color: #fff !important;
    font-family: 'Inter', sans-serif !important; min-height: 52px !important;
}
div[data-baseweb="select"] svg { fill: rgba(255,255,255,0.5) !important; }
div[data-baseweb="select"] span { color: #fff !important; font-family:'Inter',sans-serif !important; }
ul[data-baseweb="menu"] { background: #0d101f !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
li[role="option"] { color: rgba(255,255,255,0.7) !important; font-family:'Inter',sans-serif !important; }
li[role="option"]:hover { background: rgba(245,158,11,0.12) !important; color: #f59e0b !important; }
li[aria-selected="true"] { background: rgba(245,158,11,0.18) !important; color: #f59e0b !important; }

/* BUTTON */
div[data-testid="stButton"] > button {
    all: unset;
    display: block; width: 100%; box-sizing: border-box;
    text-align: center;
    background: #f59e0b !important; color: #000000 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 22px !important; letter-spacing: 3px !important;
    padding: 17px 0 !important; border-radius: 14px !important;
    cursor: pointer !important; margin-top: 12px !important;
    box-shadow: 0 0 25px rgba(245,158,11,0.6), 0 0 60px rgba(245,158,11,0.25) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover {
    background: #fbbf24 !important; color: #000 !important;
    box-shadow: 0 0 40px rgba(245,158,11,0.9), 0 0 90px rgba(245,158,11,0.4) !important;
    transform: translateY(-2px) !important;
}

/* RESULTS */
.res-outer {
    position: relative; z-index: 10;
    padding: 0 20px 60px;
    display: flex; flex-direction: column; align-items: center;
}
.res-head {
    font-family: 'Bebas Neue', sans-serif; font-size: 26px;
    color: #fff; letter-spacing: .1em;
    display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
    width: 100%; max-width: 1100px;
}
.res-head em { font-family:'Playfair Display',serif; font-style:italic; color:#f59e0b; font-size:24px; }
.pill {
    background: rgba(245,158,11,.15); border: 1px solid rgba(245,158,11,.3);
    color: #f59e0b; font-family:'Inter',sans-serif; font-size:11px; font-weight:700;
    padding: 3px 10px; border-radius: 20px;
}
.pgrid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px; width: 100%; max-width: 1100px;
}
.pcard {
    position: relative; border-radius: 12px; overflow: hidden;
    background: #111827; aspect-ratio: 2/3;
    animation: popIn .4s ease both;
    transition: transform .25s, box-shadow .25s;
    cursor: default;
}
.pcard:hover {
    transform: translateY(-8px) scale(1.04);
    box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 0 2px rgba(245,158,11,0.5);
    z-index: 5;
}
.pcard img { width: 100%; height: 100%; object-fit: cover; display: block; }
.pcard-blank {
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: linear-gradient(155deg, #1a1a2e, #16213e);
    padding: 16px; text-align: center;
    font-family: 'Bebas Neue', sans-serif; font-size: 15px;
    color: rgba(255,255,255,0.5); letter-spacing: .05em; line-height: 1.4;
}
.pcard-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.92) 0%, transparent 55%);
    opacity: 0; transition: opacity .25s;
}
.pcard:hover .pcard-overlay { opacity: 1; }
.pcard-info {
    position: absolute; bottom: 0; left: 0; right: 0;
    padding: 10px 12px 14px;
    font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500;
    color: #fff; line-height: 1.3;
    opacity: 0; transition: opacity .25s; z-index: 2;
}
.pcard:hover .pcard-info { opacity: 1; }
.pcard-num {
    position: absolute; top: 8px; left: 10px;
    font-family: 'Bebas Neue', sans-serif; font-size: 22px;
    color: #f59e0b; z-index: 2;
    text-shadow: 0 2px 8px rgba(0,0,0,0.9);
}
@keyframes popIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }

.foot {
    text-align:center; font-family:'Inter',sans-serif; font-size:9px;
    letter-spacing:.3em; color:rgba(255,255,255,.08); text-transform:uppercase;
    padding: 30px 0 20px; position:relative; z-index:10;
}
div[data-testid="stVerticalBlock"] > div { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── POSTER WALL ──
with st.spinner("🎬 Loading..."):
    wall_data = get_wall_posters(wall_titles)

wall_html = ""
for i, (title, url) in enumerate(wall_data):
    delay = i * 0.05
    if url:
        wall_html += f'<div class="wposter" style="animation-delay:{delay}s"><img src="{url}" alt="{title}" referrerpolicy="no-referrer"/></div>'
    else:
        wall_html += f'<div class="wposter" style="animation-delay:{delay}s"><div class="wposter-blank"></div></div>'

st.markdown(f"""
<div class="pwall">{wall_html}</div>
<div class="vignette"></div>
<div class="hero-wrap">
    <div class="eyebrow">CineMatch AI</div>
    <div class="htitle">𝔴𝔥𝔞𝔱'𝔰 𝔶𝔬𝔲𝔯 𝔫𝔢𝔵𝔱<br> <em>𝓜𝓞𝓥𝓘𝓔</em></div>
    <div class="hsub">Content-Based Similarity &nbsp;·&nbsp; 5000+ Films</div>
</div>
""", unsafe_allow_html=True)

# ── SEARCH ──
_, col, _ = st.columns([1, 2.2, 1])
with col:
    search_movie = st.text_input("🔍  SEARCH", placeholder="e.g. The Dark Knight, Inception, Avatar…")
    if search_movie:
        filtered_movies = movies[movies['title'].str.contains(search_movie, case=False, na=False)]['title'].tolist()
    else:
        filtered_movies = movies['title'].tolist()

    selected_movie_name = st.selectbox("🎬  SELECT MOVIE", filtered_movies)
    recommend_clicked = st.button("▶  FIND SIMILAR FILMS")

# ── RESULTS ──
if recommend_clicked:
    with st.spinner("🎬 Fetching posters..."):
        titles, posters = recommend(selected_movie_name)

    if titles:
        cards = ""
        for i, (title, poster) in enumerate(zip(titles, posters), 1):
            num = str(i).zfill(2)
            if poster:
                inner = f'<img src="{poster}" alt="{title}"/>'
            else:
                short = title[:28] + "…" if len(title) > 28 else title
                inner = f'<div class="pcard-blank">{short}</div>'

            cards += f"""<div class="pcard" style="animation-delay:{i*0.05}s">
                {inner}
                <div class="pcard-overlay"></div>
                <div class="pcard-num">{num}</div>
                <div class="pcard-info">{title}</div>
            </div>"""

        st.markdown(f"""
        <div class="res-outer">
            <div class="res-head">Because you liked <em>{selected_movie_name}</em> <span class="pill">{len(titles)} picks</span></div>
            <div class="pgrid">{cards}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No recommendations found.")

st.markdown('<div class="foot">CineMatch &nbsp;·&nbsp; AI Recommendation Engine &nbsp;·&nbsp; 2025</div>', unsafe_allow_html=True )