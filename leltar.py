import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# SZOROS KIOSZTÁS ÉS TISZTA DESIGN
st.markdown("""
    <style>
    .stNumberInput label { display: none; } /* Feliratok elrejtése a bevitelnél a helytakarékosságért */
    .total-display { font-size: 18px; font-weight: bold; color: #007bff; padding-top: 5px; }
    .termek-nev { font-size: 16px; font-weight: bold; margin-bottom: -5px; }
    .info-text { font-size: 12px; color: #777; margin-top: -5px; }
    .stDivider { margin: 5px 0px; }
    .block-container { padding-top: 2rem; }
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
for key in ['r_input', 't_input', 'z_input']:
    if key not in st.session_state: st.session_state[key] = {}

# --- FUNKCIÓ: TELJES NULLÁZÁS ---
def clear_everything(input_dict_key):
    st.session_state[input_dict_key] = {}
    # Minden widgetet nullázunk a kulcsa alapján
    for key in st.session_state.keys():
        if key.startswith(('rk_', 'rd_', 'tk_', 'td_', 'zt_', 'zb_')):
            st.session_state[key] = 0.0 if key.startswith(('zt_', 'zb_')) else 0
    st.rerun()

# --- SEGÉDFUNKCIÓ: DINAMIKUS LISTA GENERÁLÁSA (Fáziskésés nélkül) ---
def get_current_summary(prefix, dataframe, nev_col, is_leltar=False):
    summary = {}
    for idx, row in dataframe.iterrows():
        nev = str(row[nev_col]).strip()
        if is_leltar:
            teli = st.session_state.get(f"zt_{idx}", 0.0)
            bont = st.session_state.get(f"zb_{idx}", 0.0)
            total = teli + bont
            if total > 0: summary[nev] = f"{total} üveg"
        else:
            k_val = st.session_state.get(f"{prefix}k_{idx}", 0)
            d_val = st.session_state.get(f"{prefix}d_{idx}", 0)
            try: valto = float(str(row.iloc[26]).replace(',', '.'))
            except: valto = 6.0
            total = int((k_val * valto) + d_val)
            if total > 0: summary[nev] = f"{total} db"
    return summary

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# AKTUALIS LISTA MEGJELENÍTÉSE FENT
current_data = {}
if funkcio == "📦 Raktár Beszállítás":
    current_data = get_current_summary("r", df, nev_col)
    title = "Raktár"
elif funkcio == "🚚 Pult töltés":
    current_data = get_current_summary("t", df, nev_col)
    title = "Töltés"
elif funkcio == "🍹 Pult zárás":
    current_data = get_current_summary("z", df, nev_col, is_leltar=True)
    title = "Záró"

if current_data:
    with st.expander(f"📋 {title} ellenőrző lista ({len(current_data)} tétel)", expanded=True):
        cols = st.columns(4)
        for i, (k, v) in enumerate(current_data.items()):
            cols[i % 4].markdown(f"<p style='font-size:12px; margin:0;'><b>{k}:</b> {v}</p>", unsafe_allow_html=True)
        if st.button(f"🗑️ {title} lista és mezők nullázása"):
            clear_everything('r_input' if funkcio.startswith("📦") else ('t_input' if funkcio.startswith("🚚") else 'z_input'))

# --- TARTALOM ---
if funkcio != "💾 Mentés":
    kereses = st.text_input("🔍 Keresés...", "")
    
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                try: valto = float(str(row.iloc[26]).replace(',', '.'))
                except: valto = 6.0
                st.markdown(f"<p class='info-text'>{row[urt_col]} | {int(valto)} db/k</p>", unsafe_allow_html=True)
            
            if funkcio == "🍹 Pult zárás":
                with c2: val1 = st.number_input("Teli", 0.0, step=1.0, key=f"zt_{idx}")
                with c3: val2 = st.number_input("Bont", 0.0, step=0.25, key=f"zb_{idx}")
                osszes = val1 + val2
                label = "üveg"
            else:
                prefix = "rk" if "Raktár" in funkcio else "tk"
                with c2: val1 = st.number_input("K", 0, key=f"{prefix}_{idx}")
                with c3: val2 = st.number_input("D", 0, key=f"{prefix[0]}d_{idx}")
                osszes = int((val1 * valto) + val2)
                label = "db"

            with c4:
                if osszes > 0:
                    st.markdown(f"<p class='total-display'>{osszes} {label}</p>", unsafe_allow_html=True)
            st.divider()

# --- 4. MENTÉS ---
elif funkcio == "💾 Mentés":
    st.title("💾 Beküldés")
    # Itt a mentési kód...
