import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
# A Te saját Google híd linked beillesztve:
SCRIPT_URL = "https://script.google.com/macros/s/16xKwjxGK0dlHZA9_Bspu7DWv7T9Na7psy5a-gI5fLYD8_Kqx6wfhAV07/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# ADATOK BETÖLTÉSE
@st.cache_data
def load_data():
    if not os.path.exists(ALAP_FAJL): return None
    try:
        # Próbáljuk meg betölteni az alapfájlt
        df = pd.read_csv(ALAP_FAJL, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

df = load_data()

# MENTÉS GOOGLE TÁBLÁZATBA
def save_to_google(lista_adatok, sheet_name):
    payload = {
        "sheet": sheet_name,
        "rows": lista_adatok
    }
    try:
        # Adatok küldése a Google Apps Script-nek
        response = requests.post(SCRIPT_URL, json=payload)
        if response.status_code == 200:
            st.success(f"✅ Sikeresen mentve a Google Táblázatba ({sheet_name})!")
            return True
        else:
            st.error("Hiba történt a beküldés során (Google hiba).")
            return False
    except Exception as e:
        st.error(f"Nem sikerült elérni a Google-t: {e}")
        return False

if df is None:
    st.error(f"⚠️ Hiányzik a fájl a GitHubról: {ALAP_FAJL}")
    st.stop()

# Oszlop azonosítás
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["Pult töltés", "Pult zárás", "Zárás véglegesítése"])

if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}

# --- 1. PULT TÖLTÉS ---
if funkcio == "Pult töltés":
    st.title("🚚 Pult töltés")
    kereses = st.text_input("🔍 Keresés termékre...", "")
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
                with c4: st.write("**Összesen:**"); st.info(f"{int(osszes)} db")
                st.session_state.atmeneti_toltes[nev] = int(osszes)
            st.divider()

# --- 2. PULT ZÁRÁS ---
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
                    st.write("**Összesen:**")
                    val = int(uj) if uj.is_integer() else uj
                    st.info(f"{val} db")
            st.divider()

# --- 3. VÉGLEGESÍTÉS ---
elif funkcio == "Zárás véglegesítése":
    st.title("💾 Mentés a Google Táblázatba")
    
    # TÖLTÉSEK MENTÉSE
    if st.session_state.atmeneti_toltes:
        st.subheader("🚚 Mai töltések")
        t_list = [{"Termék": k, "db": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_toltes.items()]
        st.table(pd.DataFrame(t_list))
        if st.button("TÖLTÉSEK BEKÜLDÉSE"):
            if save_to_google(t_list, "Toltesek"):
                st.session_state.atmeneti_toltes = {}

    # ZÁRÁS MENTÉSE
    if st.session_state.atmeneti_leltar:
        # Csak a 0-nál nagyobb értékeket listázzuk
        z_valid = {k: v for k, v in st.session_state.atmeneti_leltar.items() if v > 0}
        if z_valid:
            st.subheader("🍹 Pult zárás")
            z_list = [{"Termék": k, "Záró": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in z_valid.items()]
            st.table(pd.DataFrame(z_list))
            if st.button("ZÁRÁS BEKÜLDÉSE"):
                if save_to_google(z_list, "Zarasok"):
                    st.session_state.atmeneti_leltar = {}
