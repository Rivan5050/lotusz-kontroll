import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# CSS a rögzített listához az oldal tetején
st.markdown("""
    <style>
    .sticky-list {
        position: fixed;
        top: 50px;
        right: 20px;
        width: 300px;
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #4e4e4e;
        z-index: 1000;
        max-height: 400px;
        overflow-y: auto;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .total-display {
        font-size: 24px;
        font-weight: bold;
        color: #00ff00;
    }
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

# Session state-ek
if 'atmeneti_raktar' not in st.session_state: st.session_state.atmeneti_raktar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}
if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}

# --- SEGÉDFUNKCIÓ: Rögzített ellenőrző lista megjelenítése ---
def show_sticky_summary(data_dict, title):
    if data_dict:
        with st.sidebar:
            st.markdown(f"### 📝 {title} (Ellenőrzés)")
            for k, v in data_dict.items():
                st.write(f"🔹 {k}: **{v} db**")
            if st.button("🗑️ Lista ürítése"):
                data_dict.clear()
                st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés és Összesítés"])

if df is None:
    st.error("⚠️ Alapfájl hiba!"); st.stop()

nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# --- 1. RAKTÁR BESZÁLLÍTÁS ---
if funkcio == "📦 Raktár Beszállítás":
    st.title("📦 Raktár Beszállítás (Karton + Darab)")
    show_sticky_summary(st.session_state.atmeneti_raktar, "Raktár érkezés")
    
    kereses = st.text_input("🔍 Keresés termékre...", "", key="search_raktar")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 1.0
        
        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])
            with c1: st.write(f"📏 {row[urt_col]} | 📦 {int(valto)} db/k")
            with c2: r_k = st.number_input("Karton", 0, step=1, key=f"r_k_{idx}")
            with c3: r_d = st.number_input("Darab", 0, step=1, key=f"r_d_{idx}")
            osszes = (r_k * valto) + r_d
            if osszes > 0:
                st.session_state.atmeneti_raktar[nev] = int(osszes)
                with c4: st.markdown(f"<p class='total-display'>{int(osszes)} db</p>", unsafe_allow_html=True)
            st.divider()

# --- 2. PULT TÖLTÉS ---
elif funkcio == "🚚 Pult töltés":
    st.title("🚚 Pult töltés (Raktár -> Pult)")
    show_sticky_summary(st.session_state.atmeneti_toltes, "Pultba felvitt")
    
    kereses = st.text_input("🔍 Keresés...", "", key="search_toltes")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 1.0
        
        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])
            with c1: st.write(f"📏 {row[urt_col]} | 📦 {int(valto)} db/k")
            with c2: k_m = st.number_input("Karton", 0, step=1, key=f"t_k_{idx}")
            with c3: d_m = st.number_input("Darab", 0, step=1, key=f"t_d_{idx}")
            osszes = (k_m * valto) + d_m
            if osszes > 0:
                st.session_state.atmeneti_toltes[nev] = int(osszes)
                with c4: st.markdown(f"<p class='total-display'>{int(osszes)} db</p>", unsafe_allow_html=True)
            st.divider()

# --- 3. PULT ZÁRÁS ---
elif funkcio == "🍹 Pult zárás":
    st.title("🍹 Pult zárás")
    show_sticky_summary(st.session_state.atmeneti_leltar, "Záró készlet")
    
    kereses = st.text_input("🔍 Keresés...", "", key="search_zaras")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.2])
            with c1: st.write(f"📏 {row[urt_col]}")
            with c2: mod = st.radio("Mód:", ["Teli (1.0)", "Bontott (0.25)"], key=f"m_{idx}", horizontal=True)
            step = 1.0 if "Teli" in mod else 0.25
            with c3:
                uj = st.number_input("Záró db", 0.0, step=step, key=f"z_{idx}", format="%.2f")
                if uj > 0: st.session_state.atmeneti_leltar[nev] = uj
            with c4:
                if uj > 0: st.markdown(f"<p class='total-display'>{uj}</p>", unsafe_allow_html=True)
            st.divider()

# --- 4. MENTÉS --- (A mentés rész változatlan, de már látod az összesítést végig)
elif funkcio == "💾 Mentés és Összesítés":
    st.title("💾 Mentés a Google Táblázatba")
    # ... (Itt a korábbi Mentés kódod fut tovább)
