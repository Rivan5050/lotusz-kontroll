import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# STÍLUS: Maximális kontraszt és olvashatóság
st.markdown("""
    <style>
    .termek-nev { font-size: 18px; font-weight: bold; color: #000 !important; margin-bottom: 0px; }
    .info-text { font-size: 13px; color: #333 !important; font-weight: 600; }
    .total-display { font-size: 22px; font-weight: bold; color: #007bff; }
    .stNumberInput label { color: #000 !important; font-weight: bold !important; font-size: 14px !important; }
    /* Ellenőrző lista stílusa */
    .summary-box { background-color: #f0f7ff; border: 2px solid #007bff; padding: 10px; border-radius: 10px; margin-bottom: 20px; }
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
def clear_current_tab(p_code):
    for key in list(st.session_state.keys()):
        if key.startswith((f"{p_code}k_", f"{p_code}d_", "zt_", "zb_")):
            st.session_state[key] = 0.0 if key.startswith('z') else 0
    st.rerun()

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Hiba: lotusz_alap.csv nem található!"); st.stop()
nev_col = df.columns[0]

p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Záró")

if funkcio != "💾 Mentés":
    st.title(f"{funkcio}")
    
    # 1. ELLENŐRZŐ LISTA ÉS TÖRLÉS GOMB (FENT, HOGY MINDIG LÁTSZON)
    summary_dict = {}
    for idx, row in df.iterrows():
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0
        
        if p_code == "z":
            t = float(st.session_state.get(f"zt_{idx}", 0))
            b = float(st.session_state.get(f"zb_{idx}", 0))
            if (t + b) > 0: summary_dict[str(row[nev_col])] = f"{t+b} üveg"
        else:
            k = int(st.session_state.get(f"{p_code}k_{idx}", 0))
            d = int(st.session_state.get(f"{p_code}d_{idx}", 0))
            if (k * valto + d) > 0: summary_dict[str(row[nev_col])] = f"{int(k * valto + d)} db"

    if summary_dict:
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.subheader(f"📋 {tab_nev} Ellenőrző Lista")
        c_list = st.columns(3)
        for i, (k, v) in enumerate(summary_dict.items()):
            c_list[i % 3].write(f"**{k}**: {v}")
        
        if st.button(f"🗑️ ÖSSZES {tab_nev.upper()} TÖRLÉSE", type="secondary", use_container_width=True):
            clear_current_tab(p_code)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. KERESŐ
    kereses = st.text_input("🔍 Keresés termékre...", "")

    st.divider()

    # 3. TERMÉKEK (BIZTONSÁGI CIKLUS - NEM ÁLL LE A LISTA)
    # Csoportosítva jelenítjük meg, hogy ne szálljon el a Streamlit
    filtered_df = df[df[nev_col].str.contains(kereses, case=False, na=False)]
    
    for idx, row in filtered_df.iterrows():
        nev = str(row[nev_col]).strip()
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='info-text'>{int(valto)} db / Karton</p>", unsafe_allow_html=True)
            
            if p_code == "z":
                v1 = col2.number_input("Teli", min_value=0.0, step=1.0, key=f"zt_{idx}")
                v2 = col3.number_input("Bont", min_value=0.0, step=0.25, key=f"zb_{idx}")
                osszes = v1 + v2
                unit = "üveg"
            else:
                v1 = col2.number_input("Karton", min_value=0, step=1, key=f"{p_code}k_{idx}")
                v2 = col3.number_input("Darab", min_value=0, step=1, key=f"{p_code}d_{idx}")
                osszes = (v1 * valto) + v2
                unit = "db"

            with col4:
                if osszes > 0:
                    st.markdown(f"<p class='total-display'>{int(osszes) if unit=='db' else osszes} {unit}</p>", unsafe_allow_html=True)
            st.markdown("---")

    # 4. MENTÉS GOMB A LISTA VÉGÉN
    if summary_dict:
        if st.button(f"🚀 {tab_nev.upper()} BEKÜLDÉSE MOST", type="primary", use_container_width=True):
            st.success(f"Adatok beküldve a Google Táblázatba! ({len(summary_dict)} tétel)")

else:
    st.title("💾 Mentés és Áttekintés")
    st.info("Itt láthatod a még be nem küldött tételeket.")
