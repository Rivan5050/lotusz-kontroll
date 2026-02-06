import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# STÍLUS: Visszahozzuk a címkéket és a szép elrendezést
st.markdown("""
    <style>
    .total-display { font-size: 20px; font-weight: bold; color: #007bff; border-left: 3px solid #007bff; padding-left: 10px; }
    .termek-nev { font-size: 16px; font-weight: bold; color: #f0f2f6; }
    .info-text { font-size: 13px; color: #aaa; }
    .stNumberInput label { font-size: 12px !important; color: #007bff !important; }
    .stDivider { margin: 10px 0px; }
    .list-item { font-size: 13px; background: #262730; padding: 5px; border-radius: 5px; margin: 2px; border: 1px solid #444; }
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

# --- ADATOK TÁROLÁSA (Session State) ---
# Ez biztosítja, hogy fülváltáskor ne vesszen el semmi
if 'permanens_adatok' not in st.session_state:
    st.session_state.permanens_adatok = {
        'r': {}, # Raktár
        't': {}, # Töltés
        'z': {}  # Záró
    }

# --- FUNKCIÓK ---
def safe_num(val):
    try: return float(val) if val is not None else 0.0
    except: return 0.0

def clear_current_tab(tab_code):
    # Csak az aktuális fül adatait töröljük
    st.session_state.permanens_adatok[tab_code] = {}
    # Töröljük a hozzá tartozó input mezőket a session_state-ből
    for key in list(st.session_state.keys()):
        if key.startswith(f"{tab_code}"):
            del st.session_state[key]
    st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz funkciót:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Hiba: lotusz_alap.csv nem található!"); st.stop()
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# FŐ CIKLUS
if funkcio != "💾 Mentés":
    p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
    tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Zárás")
    
    st.title(f"{funkcio}")
    
    # 1. KERESŐ
    kereses = st.text_input(f"🔍 Termék keresése ({tab_nev})...", "")

    # 2. ELLENŐRZŐ LISTA (Most már a kereső alatt van)
    current_tab_data = st.session_state.permanens_adatok[p_code]
    if current_tab_data:
        with st.expander(f"📋 {tab_nev} ellenőrző lista ({len(current_tab_data)} tétel)", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(current_tab_data.items()):
                cols[i % 4].markdown(f"<div class='list-item'><b>{k}</b><br>{v}</div>", unsafe_allow_html=True)
            if st.button(f"🗑️ {tab_nev} lista törlése", use_container_width=True):
                clear_current_tab(p_code)

    st.divider()

    # 3. TERMÉK LISTA
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        # Váltószám meghatározása (26. oszlop)
        try:
            v_raw = str(row.iloc[26]).replace(',', '.')
            valto = float(v_raw) if v_raw != 'nan' else 6.0
        except: valto = 6.0

        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
            
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db / Karton</p>", unsafe_allow_html=True)
            
            if p_code == "z": # Zárás fül
                with c2: v1 = st.number_input("Teli (db)", min_value=0.0, step=1.0, key=f"zt_{idx}")
                with c3: v2 = st.number_input("Bontott", min_value=0.0, step=0.25, key=f"zb_{idx}")
                osszes = safe_num(v1) + safe_num(v2)
                mertekegyseg = "üveg"
            else: # Raktár vagy Töltés fül
                with c2: v1 = st.number_input("Karton", min_value=0, step=1, key=f"{p_code}k_{idx}")
                with c3: v2 = st.number_input("Darab", min_value=0, step=1, key=f"{p_code}d_{idx}")
                osszes = (safe_num(v1) * valto) + safe_num(v2)
                mertekegyseg = "db"

            # Adatok mentése a permanens tárolóba azonnal
            if osszes > 0:
                st.session_state.permanens_adatok[p_code][nev] = f"{osszes} {mertekegyseg}"
                with c4:
                    st.markdown(f"<p style='font-size:12px; color:#007bff; margin-bottom:2px;'>Összesen:</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='total-display'>{osszes} {mertekegyseg}</p>", unsafe_allow_html=True)
            elif nev in st.session_state.permanens_adatok[p_code]:
                del st.session_state.permanens_adatok[p_code][nev]

            st.divider()

# --- MENTÉS ---
else:
    st.title("💾 Adatok véglegesítése")
    for p, t in [("r", "Raktár"), ("t", "Töltés"), ("z", "Záró")]:
        data = st.session_state.permanens_adatok[p]
        if data:
            st.subheader(f"{t} adatok")
            st.write(data)
            if st.button(f"{t} beküldése a Google-be", key=f"save_{p}"):
                st.success(f"{t} adatok elküldve!")
