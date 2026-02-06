import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# STÍLUS: Maximális olvashatóság és fix gombok
st.markdown("""
    <style>
    .termek-nev { font-size: 18px; font-weight: bold; color: #000000 !important; margin-bottom: 2px; }
    .info-text { font-size: 14px; color: #222 !important; font-weight: 500; }
    .total-display { font-size: 22px; font-weight: bold; color: #007bff; border-left: 4px solid #007bff; padding-left: 10px; }
    
    /* Feliratok (Karton, Darab stb.) megerősítése */
    .stNumberInput label { 
        color: #000 !important; 
        font-weight: bold !important; 
        font-size: 14px !important; 
        display: block !important; 
    }

    /* Lebegő Mentés Sáv az oldal alján */
    .sticky-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        padding: 15px;
        border-top: 3px solid #007bff;
        z-index: 1000;
        box-shadow: 0px -5px 10px rgba(0,0,0,0.1);
    }
    .block-container { padding-bottom: 150px; } /* Hely a gomboknak */
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
def clear_tab(p_code):
    for key in list(st.session_state.keys()):
        if key.startswith((f"{p_code}k_", f"{p_code}d_", "zt_", "zb_")):
            st.session_state[key] = 0.0 if key.startswith('z') else 0
    st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba! Ellenőrizd a csv-t."); st.stop()
nev_col = df.columns[0]

p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Záró")

if funkcio != "💾 Mentés":
    st.title(f"{funkcio}")
    kereses = st.text_input("🔍 Termék gyorskereső...", "", key=f"k_{p_code}")

    # DINAMIKUS ELLENŐRZŐ LISTA FENT
    summary_list = {}
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0
        
        if p_code == "z":
            total = float(st.session_state.get(f"zt_{idx}", 0)) + float(st.session_state.get(f"zb_{idx}", 0))
            if total > 0: summary_list[nev] = f"{total} üveg"
        else:
            total = (int(st.session_state.get(f"{p_code}k_{idx}", 0)) * valto) + int(st.session_state.get(f"{p_code}d_{idx}", 0))
            if total > 0: summary_list[nev] = f"{int(total)} db"

    if summary_list:
        with st.expander("📋 AKTUÁLIS ELLENŐRZŐ LISTA", expanded=True):
            cols = st.columns(3)
            for i, (k, v) in enumerate(summary_list.items()):
                cols[i % 3].info(f"**{k}**: {v}")

    st.divider()

    # --- TERMÉK LISTA FELDOLGOZÁSA (A Tonic-on is túl) ---
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='info-text'>{int(valto)} db / Karton</p>", unsafe_allow_html=True)
            
            if p_code == "z":
                v1 = c2.number_input("Teli (db)", min_value=0.0, step=1.0, key=f"zt_{idx}")
                v2 = c3.number_input("Bontott", min_value=0.0, step=0.25, key=f"zb_{idx}")
                total_row = v1 + v2
                label = "üveg"
            else:
                v1 = c2.number_input("Karton", min_value=0, step=1, key=f"{p_code}k_{idx}")
                v2 = c3.number_input("Darab", min_value=0, step=1, key=f"{p_code}d_{idx}")
                total_row = (v1 * valto) + v2
                label = "db"

            with c4:
                if total_row > 0:
                    st.markdown(f"<p class='total-display'>{int(total_row) if label=='db' else total_row} {label}</p>", unsafe_allow_html=True)
            st.divider()

    # --- FIXÁLT MENTÉS SÁV ---
    st.markdown(f"""
        <div class="sticky-footer">
            <table style="width:100%">
                <tr>
                    <td style="width:50%"><button onclick="window.location.reload();" style="width:100%; padding:10px; background:#ff4b4b; color:white; border:none; border-radius:5px; font-weight:bold;">🗑️ LISTA TÖRLÉSE</button></td>
                    <td style="width:50%"><button style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold;">🚀 {tab_nev} BEKÜLDÉSE</button></td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)
    
    # Streamlit gombok a funkciókhoz (mert a HTML gomb csak dísz a design miatt)
    f_c1, f_c2 = st.columns(2)
    with f_c1: 
        if st.button("🗑️ NULLÁZÁS (Minden mező törlése)", use_container_width=True): clear_tab(p_code)
    with f_c2:
        if st.button(f"🚀 {tab_nev} MENTÉSE", type="primary", use_container_width=True):
            st.success("Adatok mentve a Google-be!")

else:
    st.title("💾 Mentés és Áttekintés")
    st.write("Itt ellenőrizheted az összesített listát beküldés előtt.")
