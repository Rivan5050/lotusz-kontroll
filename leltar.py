import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# Tisztább design, kék kiemeléssel
st.markdown("""
    <style>
    .total-display { font-size: 19px; font-weight: bold; color: #007bff; border-bottom: 2px solid #007bff; }
    .info-text { font-size: 13px; color: #888; }
    .stNumberInput { margin-bottom: -10px; }
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

# Session State-ek (Adatmegőrzéshez)
for key in ['atmeneti_raktar', 'atmeneti_toltes', 'atmeneti_leltar']:
    if key not in st.session_state: st.session_state[key] = {}

# SEGÉDFUNKCIÓ: Kompakt lista és TELJES TÖRLÉS (inputok nullázása)
def show_compact_header(data_key, title):
    if st.session_state[data_key]:
        with st.expander(f"📋 {title} ellenőrző lista ({len(st.session_state[data_key])} tétel)", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(st.session_state[data_key].items()):
                cols[i % 4].markdown(f"<p style='font-size:12px; margin:0;'><b>{k}:</b> {v}</p>", unsafe_allow_html=True)
            
            if st.button(f"🗑️ Összes {title} törlése és mezők nullázása"):
                st.session_state[data_key] = {}
                st.rerun()

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]
# Űrtartalom oszlop keresése
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# --- 1. RAKTÁR BESZÁLLÍTÁS ---
if funkcio == "📦 Raktár Beszállítás":
    st.title("📦 Raktár Beszállítás")
    show_compact_header('atmeneti_raktar', "Raktár")
    kereses = st.text_input("🔍 Keresés...", "", key="s_r")
    
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        # Karton szorzó pontos kezelése (26. oszlop)
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0 # Alapértelmezett, ha hibás az adat
            
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: 
                st.markdown(f"**{nev}**")
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db/karton</p>", unsafe_allow_html=True)
            with c2: r_k = st.number_input("Karton", 0, key=f"rk_{idx}")
            with c3: r_d = st.number_input("Darab", 0, key=f"rd_{idx}")
            
            osszes = int((r_k * valto) + r_d)
            if osszes > 0:
                st.session_state.atmeneti_raktar[nev] = f"{osszes} db"
                with c4: st.markdown(f"<p class='total-display'>{osszes} db</p>", unsafe_allow_html=True)
            elif nev in st.session_state.atmeneti_raktar:
                del st.session_state.atmeneti_raktar[nev]
            st.divider()

# --- 2. PULT TÖLTÉS ---
elif funkcio == "🚚 Pult töltés":
    st.title("🚚 Pult töltés")
    show_compact_header('atmeneti_toltes', "Töltés")
    kereses = st.text_input("🔍 Keresés...", "", key="s_t")
    
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: 
                st.markdown(f"**{nev}**")
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db/karton</p>", unsafe_allow_html=True)
            with c2: t_k = st.number_input("Karton", 0, key=f"tk_{idx}")
            with c3: t_d = st.number_input("Darab", 0, key=f"td_{idx}")
            
            osszes = int((t_k * valto) + t_d)
            if osszes > 0:
                st.session_state.atmeneti_toltes[nev] = f"{osszes} db"
                with c4: st.markdown(f"<p class='total-display'>{osszes} db</p>", unsafe_allow_html=True)
            elif nev in st.session_state.atmeneti_toltes:
                del st.session_state.atmeneti_toltes[nev]
            st.divider()

# --- 3. PULT ZÁRÁS ---
elif funkcio == "🍹 Pult zárás":
    st.title("🍹 Pult zárás")
    show_compact_header('atmeneti_leltar', "Záró")
    kereses = st.text_input("🔍 Keresés...", "", key="s_z")
    
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: 
                st.markdown(f"**{nev}**")
                st.markdown(f"<p class='info-text'>{row[urt_col]}</p>", unsafe_allow_html=True)
            with c2: z_teli = st.number_input("Teli (db)", 0.0, step=1.0, key=f"zt_{idx}")
            with c3: z_bont = st.number_input("Bontott (0.25)", 0.0, step=0.25, key=f"zb_{idx}")
            
            vegosszeg = z_teli + z_bont
            if vegosszeg > 0:
                st.session_state.atmeneti_leltar[nev] = f"{vegosszeg} üveg"
                with c4: st.markdown(f"<p class='total-display'>{vegosszeg} üveg</p>", unsafe_allow_html=True)
            elif nev in st.session_state.atmeneti_leltar:
                del st.session_state.atmeneti_leltar[nev]
            st.divider()

# --- 4. MENTÉS ---
elif funkcio == "💾 Mentés":
    st.title("💾 Beküldés a Google Táblázatba")
    # Ide jön a már működő requests.post kódod a session_state-ek ürítésével...
