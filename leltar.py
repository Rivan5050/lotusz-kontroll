import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# KONTRASZTOS STÍLUS - Fehér háttérhez igazítva
st.markdown("""
    <style>
    /* Terméknév: Erős és olvasható */
    .termek-nev { font-size: 18px; font-weight: bold; color: #111; margin-bottom: 0px; }
    .info-text { font-size: 13px; color: #444; font-weight: 500; }
    
    /* Összesítő: Kék és nagy */
    .total-display { font-size: 22px; font-weight: bold; color: #007bff; }
    
    /* Ellenőrző lista tétel */
    .list-item { 
        background-color: #f0f8ff; 
        border: 1px solid #007bff; 
        padding: 8px; 
        border-radius: 5px; 
        color: #111;
        font-weight: bold;
        margin: 5px;
    }
    
    /* Input feliratok erősítése */
    .stNumberInput label { color: #111 !important; font-weight: bold !important; }
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

# --- FUNKCIÓK ---
def safe_num(val):
    try: return float(val) if val is not None else 0.0
    except: return 0.0

def clear_tab(p_code):
    # Minden kapcsolódó session kulcs törlése
    for key in list(st.session_state.keys()):
        if key.startswith((f"{p_code}k_", f"{p_code}d_", f"zt_", f"zb_")):
            st.session_state[key] = 0.0 if key.startswith('z') else 0
    st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# --- ADATGYŰJTÉS ÉS MEGJELENÍTÉS ---
p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Zárás")

st.title(f"{funkcio}")

# 1. KERESŐ
kereses = st.text_input("🔍 Keresés termékre...", "")

# 2. DINAMIKUS ELLENŐRZŐ LISTA (AZONNALI FRISSÍTÉSSEL)
summary_list = {}
for idx, row in df.iterrows():
    nev = str(row[nev_col]).strip()
    try:
        v_raw = str(row.iloc[26]).replace(',', '.')
        valto = float(v_raw) if v_raw != 'nan' else 6.0
    except: valto = 6.0

    if p_code == "z":
        v1 = st.session_state.get(f"zt_{idx}", 0.0)
        v2 = st.session_state.get(f"zb_{idx}", 0.0)
        total = safe_num(v1) + safe_num(v2)
        if total > 0: summary_list[nev] = f"{total} üveg"
    else:
        v1 = st.session_state.get(f"{p_code}k_{idx}", 0)
        v2 = st.session_state.get(f"{p_code}d_{idx}", 0)
        total = (safe_num(v1) * valto) + safe_num(v2)
        if total > 0: summary_list[nev] = f"{int(total)} db"

if summary_list:
    with st.expander(f"📋 {tab_nev} ellenőrző lista ({len(summary_list)} tétel)", expanded=True):
        cols = st.columns(4)
        for i, (k, v) in enumerate(summary_list.items()):
            cols[i % 4].markdown(f"<div class='list-item'>{k}: {v}</div>", unsafe_allow_html=True)
        if st.button(f"🗑️ {tab_nev} adatok nullázása", use_container_width=True):
            clear_tab(p_code)

st.divider()

# 3. TERMÉKBEVITEL
for idx, row in df.iterrows():
    nev = str(row[nev_col]).strip()
    if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
    
    try:
        v_raw = str(row.iloc[26]).replace(',', '.')
        valto = float(v_raw) if v_raw != 'nan' else 6.0
    except: valto = 6.0

    with st.container():
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        with c1:
            st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db / Karton</p>", unsafe_allow_html=True)
        
        if p_code == "z":
            with c2: v1 = st.number_input("Teli", min_value=0.0, step=1.0, key=f"zt_{idx}")
            with c3: v2 = st.number_input("Bontott", min_value=0.0, step=0.25, key=f"zb_{idx}")
            osszes = safe_num(v1) + safe_num(v2)
            label = "üveg"
        else:
            with c2: v1 = st.number_input("Karton", min_value=0, step=1, key=f"{p_code}k_{idx}")
            with c3: v2 = st.number_input("Darab", min_value=0, step=1, key=f"{p_code}d_{idx}")
            osszes = (safe_num(v1) * valto) + safe_num(v2)
            label = "db"

        with c4:
            if osszes > 0:
                st.markdown(f"<p style='font-size:11px; color:#555; margin-bottom:0;'>Összeg:</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='total-display'>{int(osszes) if label=='db' else osszes} {label}</p>", unsafe_allow_html=True)
        st.divider()
