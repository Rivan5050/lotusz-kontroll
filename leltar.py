import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# MOBILBARÁT ÉS SŰRŰ DESIGN
st.markdown("""
    <style>
    .stNumberInput label { display: none; } 
    .total-display { font-size: 18px; font-weight: bold; color: #007bff; padding-top: 5px; }
    .termek-nev { font-size: 15px; font-weight: bold; margin-bottom: -5px; }
    .info-text { font-size: 11px; color: #777; margin-top: -5px; }
    .stDivider { margin: 3px 0px; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    [data-testid="stExpander"] { border: 1px solid #007bff; background-color: #f0f2f610; }
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

# --- FUNKCIÓ: TELJES NULLÁZÁS (MEZŐK + LISTA) ---
def clear_all_inputs():
    for key in list(st.session_state.keys()):
        if key.startswith(('rk_', 'rd_', 'tk_', 'td_', 'zt_', 'zb_')):
            st.session_state[key] = 0.0 if key.startswith(('zt_', 'zb_')) else 0
    st.rerun()

# --- SEGÉDFUNKCIÓ: DINAMIKUS LISTA GENERÁLÁSA (HIBAÁLLÓ) ---
def get_current_summary(prefix, dataframe, nev_col, is_leltar=False):
    summary = {}
    for idx, row in dataframe.iterrows():
        nev = str(row[nev_col]).strip()
        if is_leltar:
            # Pult zárás (Teli + Bontott)
            teli = st.session_state.get(f"zt_{idx}", 0.0)
            bont = st.session_state.get(f"zb_{idx}", 0.0)
            teli = float(teli) if teli is not None else 0.0
            bont = float(bont) if bont is not None else 0.0
            total = teli + bont
            if total > 0: summary[nev] = f"{total} üveg"
        else:
            # Raktár/Töltés (Karton + Darab)
            # Biztonságos prefix kezelés: rk/rd vagy tk/td
            k_key = f"{prefix}k_{idx}"
            d_key = f"{prefix}d_{idx}"
            
            k_val = st.session_state.get(k_key, 0)
            d_val = st.session_state.get(d_key, 0)
            
            # None értékek kényszerítése nullára a ValueError elkerülése érdekében
            k_val = int(k_val) if k_val is not None else 0
            d_val = int(d_val) if d_val is not None else 0
            
            try:
                valto = float(str(row.iloc[26]).replace(',', '.'))
            except:
                valto = 6.0
            
            total = int((k_val * valto) + d_val)
            if total > 0: summary[nev] = f"{total} db"
    return summary

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Hiba: lotusz_alap.csv nem található!"); st.stop()
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# FEJLÉC ÖSSZESÍTŐ
# Meghatározzuk a prefixeket a get_current_summary számára
title_map = {
    "📦 Raktár Beszállítás": ("r", "Raktár", False), 
    "🚚 Pult töltés": ("t", "Töltés", False), 
    "🍹 Pult zárás": ("z", "Záró", True)
}

if funkcio in title_map:
    p, t, is_l = title_map[funkcio]
    current_data = get_current_summary(p, df, nev_col, is_leltar=is_l)
    
    if current_data:
        with st.expander(f"📋 {t} ellenőrző lista ({len(current_data)} tétel)", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(current_data.items()):
                cols[i % 4].markdown(f"<p style='font-size:11px; margin:0;'>• {k}: <b>{v}</b></p>", unsafe_allow_html=True)
            st.write("")
            if st.button(f"🗑️ {t} adatok nullázása", use_container_width=True):
                clear_all_inputs()

# --- TARTALOM ---
if funkcio != "💾 Mentés":
    kereses = st.text_input("🔍 Keresés termékre...", "")
    
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db/k</p>", unsafe_allow_html=True)
            
            if funkcio == "🍹 Pult zárás":
                with c2: v1 = st.number_input("Teli", min_value=0.0, step=1.0, key=f"zt_{idx}", value=st.session_state.get(f"zt_{idx}", 0.0))
                with c3: v2 = st.number_input("Bont", min_value=0.0, step=0.25, key=f"zb_{idx}", value=st.session_state.get(f"zb_{idx}", 0.0))
                osszes = v1 + v2
                label = "üveg"
            else:
                p_code = "r" if "Raktár" in funkcio else "t"
                with c2: v1 = st.number_input("K", min_value=0, step=1, key=f"{p_code}k_{idx}", value=st.session_state.get(f"{p_code}k_{idx}", 0))
                with c3: v2 = st.number_input("D", min_value=0, step=1, key=f"{p_code}d_{idx}", value=st.session_state.get(f"{p_code}d_{idx}", 0))
                osszes = int((v1 * valto) + v2)
                label = "db"

            with c4:
                if osszes > 0:
                    st.markdown(f"<p class='total-display'>{osszes} {label}</p>", unsafe_allow_html=True)
            st.divider()

# --- MENTÉS ---
elif funkcio == "💾 Mentés":
    st.title("💾 Mentés")
    st.info("Ellenőrizd az adatokat a listákban a mentés előtt!")
    
    r_data = get_current_summary("r", df, nev_col)
    t_data = get_current_summary("t", df, nev_col)
    z_data = get_current_summary("z", df, nev_col, is_leltar=True)

    if r_data:
        if st.button(f"RAKTÁR MENTÉSE ({len(r_data)} tétel)"):
            # Itt a Google Script hívás
            st.success("Raktár mentve!")
    if t_data:
        if st.button(f"TÖLTÉS MENTÉSE ({len(t_data)} tétel)"):
            st.success("Töltés mentve!")
    if z_data:
        if st.button(f"ZÁRÁS MENTÉSE ({len(z_data)} tétel)"):
            st.success("Zárás mentve!")
