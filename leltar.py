import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# STÍLUS (Kontrasztos, erős színek)
st.markdown("""
    <style>
    .termek-nev { font-size: 18px; font-weight: bold; color: #111; margin-bottom: 0px; }
    .info-text { font-size: 13px; color: #444; font-weight: bold; }
    .total-display { font-size: 22px; font-weight: bold; color: #007bff; }
    .list-item { 
        background-color: #f0f8ff; border: 1px solid #007bff; 
        padding: 8px; border-radius: 5px; color: #111; font-weight: bold; margin: 5px;
    }
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

# --- SEGÉDFUNKCIÓK ---
def safe_num(val):
    try: return float(val) if val is not None else 0.0
    except: return 0.0

def clear_tab(p_code):
    for key in list(st.session_state.keys()):
        if key.startswith((f"{p_code}k_", f"{p_code}d_", f"zt_", f"zb_")):
            st.session_state[key] = 0.0 if key.startswith('z') else 0
    st.rerun()

def send_to_google(data_dict, sheet_name):
    if not data_dict:
        st.error("Nincs elküldhető adat!")
        return
    payload = {
        "sheet": sheet_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data": data_dict
    }
    try:
        res = requests.post(SCRIPT_URL, json=payload)
        if res.status_code == 200: st.success(f"✅ {sheet_name} adatok sikeresen mentve!")
        else: st.error("Hiba a mentés során!")
    except: st.error("Nem sikerült elérni a szervert.")

# --- MENÜ ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés"])

if df is None: st.error("Fájl hiba!"); st.stop()
nev_col = df.columns[0]

# --- ADATFELDOLGOZÁS ---
p_code = "r" if "Raktár" in funkcio else ("t" if "Töltés" in funkcio else "z")
tab_nev = "Raktár" if p_code == "r" else ("Töltés" if p_code == "t" else "Záró")

if funkcio != "💾 Mentés":
    st.title(f"{funkcio}")
    kereses = st.text_input("🔍 Keresés termékre...", "", key=f"search_{p_code}")

    # DINAMIKUS LISTA ÉS ÖSSZESÍTŐ
    summary_list = {}
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        try:
            v_raw = str(row.iloc[26]).replace(',', '.')
            valto = float(v_raw) if v_raw != 'nan' else 6.0
        except: valto = 6.0

        if p_code == "z":
            total = safe_num(st.session_state.get(f"zt_{idx}", 0)) + safe_num(st.session_state.get(f"zb_{idx}", 0))
            if total > 0: summary_list[nev] = f"{total} üveg"
        else:
            total = (safe_num(st.session_state.get(f"{p_code}k_{idx}", 0)) * valto) + safe_num(st.session_state.get(f"{p_code}d_{idx}", 0))
            if total > 0: summary_list[nev] = f"{int(total)} db"

    if summary_list:
        with st.expander(f"📋 {tab_nev} ellenőrző lista", expanded=True):
            cols = st.columns(4)
            for i, (k, v) in enumerate(summary_list.items()):
                cols[i % 4].markdown(f"<div class='list-item'>{k}: {v}</div>", unsafe_allow_html=True)
            if st.button(f"🗑️ Mezők nullázása", use_container_width=True):
                clear_tab(p_code)

    st.divider()

    # TERMÉK LISTA
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        try:
            valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 6.0

        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
            with c1:
                st.markdown(f"<p class='termek-nev'>{nev}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='info-text'>{int(valto)} db/Karton</p>", unsafe_allow_html=True)
            
            if p_code == "z":
                v1 = st.number_input("Teli", min_value=0.0, step=1.0, key=f"zt_{idx}")
                v2 = st.number_input("Bont", min_value=0.0, step=0.25, key=f"zb_{idx}")
                osszes = v1 + v2
                unit = "üveg"
            else:
                v1 = st.number_input("Karton", min_value=0, step=1, key=f"{p_code}k_{idx}")
                v2 = st.number_input("Darab", min_value=0, step=1, key=f"{p_code}d_{idx}")
                osszes = (v1 * valto) + v2
                unit = "db"

            with c4:
                if osszes > 0:
                    st.markdown(f"<p class='total-display'>{int(osszes) if unit=='db' else osszes} {unit}</p>", unsafe_allow_html=True)
            st.divider()

    # MENTÉS GOMB AZ OLDAL ALJÁN
    if summary_list:
        st.write("### ✅ Minden rendben?")
        if st.button(f"🚀 {tab_nev} ADATOK BEKÜLDÉSE", use_container_width=True, type="primary"):
            send_to_google(summary_list, tab_nev)

else:
    st.title("💾 Összesített állapot")
    st.info("Ezen a fülön azokat az adatokat látod, amiket még nem küldtél be.")
    # Itt csak egy gyors áttekintő marad...
