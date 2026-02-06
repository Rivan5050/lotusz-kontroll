import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# Stílus beállítások
st.markdown("""
    <style>
    .total-display { font-size: 19px; font-weight: bold; color: #007bff; }
    .info-text { font-size: 13px; color: #888; margin-top: -15px; }
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

# Session State inicializálás
if 'atmeneti_raktar' not in st.session_state: st.session_state.atmeneti_raktar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}
if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}

# --- FUNKCIÓ: LISTA ÉS MEZŐK TELJES NULLÁZÁSA ---
def clear_all_inputs(data_key):
    # Töröljük a listát
    st.session_state[data_key] = {}
    # Töröljük az összes widget értékét a session_state-ből
    for key in st.session_state.keys():
        if key.startswith(('rk_', 'rd_', 'tk_', 'td_', 'zt_', 'zb_')):
            st.session_state[key] = 0 if not key.startswith(('zt_', 'zb_')) else 0.0
    st.rerun()

# SEGÉDFUNKCIÓ: Kompakt lista fejléc
def show_compact_header(data_key, title):
    if st.session_state[data_key]:
        with st.expander(f"📋 {title} ellenőrző lista ({len(st.session_state[data_key])} tétel)", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(st.session_state[data_key].items()):
                cols[i % 4].markdown(f"<p style='font-size:12px; margin:0;'><b>{k}:</b> {v}</p>", unsafe_allow_html=True)
            
            if st.button(f"🗑️ Összes {title} törlése és MEZŐK NULLÁZÁSA"):
                clear_all_inputs(data_key)

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# --- 1. RAKTÁR BESZÁLLÍTÁS ---
if funkcio == "📦 Raktár Beszállítás":
    st.title("📦 Raktár Beszállítás")
    show_compact_header('atmeneti_raktar', "Raktár")
    kereses = st.text_input("🔍 Keresés...", "", key="s_r")
    
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
            # on_change használata az azonnali frissítéshez
            r_k = st.number_input("Karton", 0, key=f"rk_{idx}")
            r_d = st.number_input("Darab", 0, key=f"rd_{idx}")
            
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
            t_k = st.number_input("Karton", 0, key=f"tk_{idx}")
            t_d = st.number_input("Darab", 0, key=f"td_{idx}")
            
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
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
            with c1: 
                st.markdown(f"**{nev}**")
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db/karton</p>", unsafe_allow_html=True)
            z_teli = st.number_input("Teli (db)", 0.0, step=1.0, key=f"zt_{idx}")
            z_bont = st.number_input("Bontott (0.25)", 0.0, step=0.25, key=f"zb_{idx}")
            
            vegosszeg = z_teli + z_bont
            if vegosszeg > 0:
                st.session_state.atmeneti_leltar[nev] = f"{vegosszeg} üveg"
                with c4: st.markdown(f"<p class='total-display'>{vegosszeg} üveg</p>", unsafe_allow_html=True)
            elif nev in st.session_state.atmeneti_leltar:
                del st.session_state.atmeneti_leltar[nev]
            st.divider()

# --- 4. MENTÉS ---
elif funkcio == "💾 Mentés":
    st.title("💾 Mentés a Google Táblázatba")
    # A beküldési logika változatlan...
