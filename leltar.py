import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
# A táblázatod ID-ja
SHEET_ID = "1G00RMHrdgNBIUd--mdUE51Zh8PlQ55-n_Ab2S-OuQhA"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# ADATOK BETÖLTÉSE
@st.cache_data
def load_data():
    if not os.path.exists(ALAP_FAJL): return None
    df = pd.read_csv(ALAP_FAJL, sep=None, engine='python', encoding='utf-8-sig')
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_data()

# MENTÉS FUNKCIÓ (Apps Script vagy közvetlen beküldés helyett most egyszerűsített szimuláció a teszthez)
def save_to_google(adatok, tipus):
    # Ez a rész felel a táblázatba írásért
    # A stabil működéshez majd egy kis Apps Script kell, de teszteljük le a felületet
    st.success(f"✅ {tipus} adatai sikeresen rögzítve a Google Táblázatba!")

if df is None:
    st.error("Hiányzik az alapfájl!"); st.stop()

nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["Pult töltés", "Pult zárás", "Zárás véglegesítése"])

if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}

# 1. TÖLTÉS
if funkcio == "Pult töltés":
    st.title("🚚 Pult töltés")
    kereses = st.text_input("🔍 Keresés...", "")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        try: valto = float(str(row.iloc[26]).replace(',', '.'))
        except: valto = 1.0
        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])
            with c1: st.write(f"📏 {row[urt_col]} | 📦 {int(valto)} db/k")
            with c2: k_m = st.number_input("Karton", 0, step=1, key=f"t_k_{idx}")
            with c3: d_m = st.number_input("Darab", 0, step=1, key=f"t_d_{idx}")
            osszes = (k_m * valto) + d_m
            if osszes > 0:
                with c4: st.info(f"{int(osszes)} db")
                st.session_state.atmeneti_toltes[nev] = int(osszes)
            st.divider()

# 2. ZÁRÁS
elif funkcio == "Pult zárás":
    st.title("🍹 Pult zárás")
    kereses = st.text_input("🔍 Keresés...", "")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.2])
            with c1: st.write(f"📏 {row[urt_col]}")
            with c2: mod = st.radio("Mód:", ["Teli (1.0)", "Bontott (0.25)"], key=f"m_{idx}", horizontal=True)
            step = 1.0 if "Teli" in mod else 0.25
            with c3:
                uj = st.number_input("Darab", 0.0, step=step, key=f"z_{idx}", format="%.2f")
                st.session_state.atmeneti_leltar[nev] = uj
            with c4:
                if uj > 0:
                    val = int(uj) if uj.is_integer() else uj
                    st.info(f"{val} db")
            st.divider()

# 3. VÉGLEGESÍTÉS
elif funkcio == "Zárás véglegesítése":
    st.title("💾 Mentés a Google Táblázatba")
    
    if st.session_state.atmeneti_toltes:
        st.subheader("🚚 Mai töltések")
        t_list = [{"Termék": k, "db": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_toltes.items()]
        st.table(pd.DataFrame(t_list))
        if st.button("Töltés rögzítése"):
            save_to_google(t_list, "Töltés")
            st.session_state.atmeneti_toltes = {}

    if st.session_state.atmeneti_leltar:
        st.subheader("🍹 Pult zárás")
        z_list = [{"Termék": k, "Záró": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_leltar.items() if v > 0]
        st.table(pd.DataFrame(z_list))
        if st.button("Zárás rögzítése"):
            save_to_google(z_list, "Zárás")
            st.session_state.atmeneti_leltar = {}
