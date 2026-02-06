import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# Sűrűbb, helytakarékos stílus és kék jelzések
st.markdown("""
    <style>
    .total-display { font-size: 18px; font-weight: bold; color: #007bff; }
    .sticky-header {
        background-color: #1e1e1e;
        padding: 5px 15px;
        border-radius: 5px;
        border: 1px solid #333;
        font-size: 13px;
        line-height: 1.2;
    }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 14px !important; font-weight: bold; }
    .stNumberInput { margin-bottom: -15px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not os.path.exists(ALAP_FAJL): return None
    try:
        df = pd.read_csv(ALAP_FAJL, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

df = load_data()

# Session State-ek inicializálása (hogy ne vesszen el váltáskor)
if 'atmeneti_raktar' not in st.session_state: st.session_state.atmeneti_raktar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}
if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}

# SEGÉDFUNKCIÓ: Kompakt lista az oldal tetején
def show_compact_header(data_dict, title, color="#007bff"):
    if data_dict:
        with st.expander(f"📝 {title} ellenőrző lista ({len(data_dict)} tétel)", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(data_dict.items()):
                cols[i % 4].markdown(f"<p style='font-size:12px; margin:0;'><b>{k}:</b> {v}</p>", unsafe_allow_html=True)
            if st.button(f"Minden {title} törlése", key=f"del_{title}"):
                data_dict.clear()
                st.rerun()

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés és Összesítés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]

# --- 1. RAKTÁR BESZÁLLÍTÁS ---
if funkcio == "📦 Raktár Beszállítás":
    st.title("📦 Raktár Beszállítás")
    show_compact_header(st.session_state.atmeneti_raktar, "Raktár")
    kereses = st.text_input("🔍 Keresés...", "", key="s_r")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        valto = float(str(row.iloc[26]).replace(',', '.')) if pd.notnull(row.iloc[26]) else 1.0
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: st.write(f"**{nev}**")
            with c2: r_k = st.number_input("Karton", 0, key=f"rk_{idx}")
            with c3: r_d = st.number_input("Darab", 0, key=f"rd_{idx}")
            osszes = (r_k * valto) + r_d
            if osszes > 0:
                st.session_state.atmeneti_raktar[nev] = int(osszes)
                with c4: st.markdown(f"<p class='total-display'>{int(osszes)} db</p>", unsafe_allow_html=True)
            st.divider()

# --- 2. PULT TÖLTÉS ---
elif funkcio == "🚚 Pult töltés":
    st.title("🚚 Pult töltés")
    show_compact_header(st.session_state.atmeneti_toltes, "Töltés")
    kereses = st.text_input("🔍 Keresés...", "", key="s_t")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        valto = float(str(row.iloc[26]).replace(',', '.')) if pd.notnull(row.iloc[26]) else 1.0
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: st.write(f"**{nev}**")
            with c2: t_k = st.number_input("Karton", 0, key=f"tk_{idx}")
            with c3: t_d = st.number_input("Darab", 0, key=f"td_{idx}")
            osszes = (t_k * valto) + t_d
            if osszes > 0:
                st.session_state.atmeneti_toltes[nev] = int(osszes)
                with c4: st.markdown(f"<p class='total-display'>{int(osszes)} db</p>", unsafe_allow_html=True)
            st.divider()

# --- 3. PULT ZÁRÁS (JAVÍTOTT: TELI + BONTOTT EGYSZERRE) ---
elif funkcio == "🍹 Pult zárás":
    st.title("🍹 Pult zárás")
    show_compact_header(st.session_state.atmeneti_leltar, "Záró")
    kereses = st.text_input("🔍 Keresés...", "", key="s_z")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: st.write(f"**{nev}**")
            with c2: z_teli = st.number_input("Teli (db)", 0.0, step=1.0, key=f"zt_{idx}")
            with c3: z_bont = st.number_input("Bontott (0.25)", 0.0, step=0.25, key=f"zb_{idx}")
            vegosszeg = z_teli + z_bont
            if vegosszeg > 0:
                st.session_state.atmeneti_leltar[nev] = vegosszeg
                with c4: st.markdown(f"<p class='total-display'>{vegosszeg}</p>", unsafe_allow_html=True)
            st.divider()

# --- 4. MENTÉS ---
elif funkcio == "💾 Mentés és Összesítés":
    st.title("💾 Mentés")
    # Itt a mentési kód, ami beküldi a session_state-eket a Google-be
    # (Az előzőleg bevált mentési logikád változatlanul ide jön)
    if st.button("RAKTÁR MENTÉSE"):
        # requests.post(...)
        st.success("Mentve!")
