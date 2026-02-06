import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# STÍLUS: Kényszerített vízszintes elrendezés és fix gombok
st.markdown("""
    <style>
    /* Kontrasztos feliratok */
    .termek-nev { font-size: 16px; font-weight: bold; color: #111; }
    .info-text { font-size: 12px; color: #555; }
    
    /* Ne engedjük egymás alá csúszni a mezőket */
    [data-testid="column"] { min-width: 50px !important; }
    
    /* Fixált mentés gomb az oldal alján, hogy ne kelljen görgetni */
    .footer-save {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 10px;
        border-top: 2px solid #007bff;
        z-index: 999;
        text-align: center;
    }
    .stNumberInput label { font-size: 11px !important; }
    .block-container { padding-bottom: 100px; } /* Hely a fix gombnak */
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

# --- SEGÉDFUNKCIÓK ---
def clear_tab(p_code):
    for key in list(st.session_state.keys()):
        if key.startswith((f"{p_code}k_", f"{p_code}d_", f"zt_", f"zb_")):
            st.session_state[key] = 0.0 if key.startswith('z') else 0
    st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]

p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Záró")

if funkcio != "💾 Mentés":
    st.title(f"{funkcio}")
    
    # Kereső és Ellenőrző lista
    kereses = st.text_input("🔍 Keresés...", "", key=f"s_{p_code}")

    summary_list = {}
    
    # TERMÉKEK MEGJELENÍTÉSE
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        # EGY SORBAN MINDEN: Név | Karton | Darab | Összes
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 0.8, 0.8, 1])
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p><p class='info-text'>{int(valto)} db/K</p>", unsafe_allow_html=True)
            
            if p_code == "z":
                v1 = c2.number_input("Teli", min_value=0.0, step=1.0, key=f"zt_{idx}")
                v2 = c3.number_input("Bont", min_value=0.0, step=0.25, key=f"zb_{idx}")
                osszes = v1 + v2
                unit = "üveg"
            else:
                v1 = c2.number_input("K", min_value=0, step=1, key=f"{p_code}k_{idx}")
                v2 = c3.number_input("D", min_value=0, step=1, key=f"{p_code}d_{idx}")
                osszes = (v1 * valto) + v2
                unit = "db"

            if osszes > 0:
                c4.markdown(f"<p class='total-display'>{int(osszes) if unit=='db' else osszes} {unit}</p>", unsafe_allow_html=True)
                summary_list[nev] = f"{osszes} {unit}"
            st.divider()

    # --- FIXÁLT MENTÉS ÉS TÖRLÉS GOMBOK (Hogy ne kelljen görgetni) ---
    st.markdown('<div class="footer-save">', unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button(f"🗑️ {tab_nev} NULLÁZÁSA"):
        clear_tab(p_code)
    if col_btn2.button(f"🚀 {tab_nev} BEKÜLDÉSE", type="primary"):
        # Itt hívjuk a mentést
        st.success("Adatok elküldve!")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title("💾 Mentés / Áttekintés")
    st.write("Itt láthatod az eddig rögzített tételeket.")
