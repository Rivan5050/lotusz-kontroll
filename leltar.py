import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

@st.cache_data
def load_data():
    if not os.path.exists(ALAP_FAJL): return None
    try:
        df = pd.read_csv(ALAP_FAJL, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

df = load_data()

# MENTÉS FUNKCIÓ
def save_to_google(lista_adatok, sheet_name):
    payload = {"sheet": sheet_name, "rows": lista_adatok}
    try:
        response = requests.post(SCRIPT_URL, json=payload)
        if response.status_code == 200:
            st.success(f"✅ Sikeresen mentve: {sheet_name}")
            return True
        else:
            st.error("Hiba történt a küldés során.")
            return False
    except Exception as e:
        st.error(f"Hiba: {e}")
        return False

if df is None:
    st.error("⚠️ Hiányzik az alapfájl!"); st.stop()

nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# MENÜ - Visszaállítva az átlátható szerkezet
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés és Összesítés"])

# Session state-ek az adatok megőrzéséhez
if 'atmeneti_raktar' not in st.session_state: st.session_state.atmeneti_raktar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}
if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}

# --- 1. RAKTÁR BESZÁLLÍTÁS (LISTÁS) ---
if funkcio == "📦 Raktár Beszállítás":
    st.title("📦 Raktár Beszállítás (Nagyker -> Raktár)")
    kereses = st.text_input("🔍 Keresés...", "", key="search_raktar")
    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", ""] or kereses.lower() not in nev.lower(): continue
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1: st.markdown(f"**{nev}**")
            with c2: n_m = st.number_input("Beérkezett (db)", 0, step=1, key=f"r_{idx}")
            if n_m > 0:
                st.session_state.atmeneti_raktar[nev] = n_m
            st.divider()

# --- 2. PULT TÖLTÉS (LISTÁS) ---
elif funkcio == "🚚 Pult töltés":
    st.title("🚚 Pult töltés (Raktár -> Pult)")
    kereses = st.text_input("🔍 Keresés...", "", key="search_toltes")
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
                st.session_state.atmeneti_toltes[nev] = int(osszes)
                with c4: st.info(f"{int(osszes)} db")
            st.divider()

# --- 3. PULT ZÁRÁS (LISTÁS) ---
elif funkcio == "🍹 Pult zárás":
    st.title("🍹 Pult zárás")
    kereses = st.text_input("🔍 Keresés...", "", key="search_zaras")
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
                uj = st.number_input("Záró db", 0.0, step=step, key=f"z_{idx}", format="%.2f")
                if uj > 0: st.session_state.atmeneti_leltar[nev] = uj
            with c4:
                if uj > 0: st.info(f"{uj} db")
            st.divider()

# --- 4. MENTÉS ÉS ÖSSZESÍTÉS ---
elif funkcio == "💾 Mentés és Összesítés":
    st.title("💾 Adatok véglegesítése")
    
    # RAKTÁR LISTA
    if st.session_state.atmeneti_raktar:
        st.subheader("📦 Raktárba érkezett")
        r_list = [{"Termék": k, "db": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_raktar.items()]
        st.table(pd.DataFrame(r_list))
        if st.button("RAKTÁR MENTÉSE"):
            if save_to_google(r_list, "Raktar"): st.session_state.atmeneti_raktar = {}

    # TÖLTÉS LISTA
    if st.session_state.atmeneti_toltes:
        st.subheader("🚚 Pultba töltve")
        t_list = [{"Termék": k, "db": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_toltes.items()]
        st.table(pd.DataFrame(t_list))
        if st.button("TÖLTÉSEK MENTÉSE"):
            if save_to_google(t_list, "Toltesek"): st.session_state.atmeneti_toltes = {}

    # ZÁRÁS LISTA
    if st.session_state.atmeneti_leltar:
        st.subheader("🍹 Pult záró készlet")
        z_list = [{"Termék": k, "Záró": v, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.atmeneti_leltar.items()]
        st.table(pd.DataFrame(z_list))
        if st.button("ZÁRÁS MENTÉSE"):
            if save_to_google(z_list, "Zarasok"): st.session_state.atmeneti_leltar = {}
