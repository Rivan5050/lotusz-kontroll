import streamlit as st
import pandas as pd
import os
from datetime import datetime

# KONFIGURÁCIÓ
ALAP_FAJL = "lotusz_alap.csv"
ADATBAZIS_ZARAS = "lotusz_zarasok.csv"
ADATBAZIS_TOLTES = "lotusz_toltesek.csv"

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

if df is None:
    st.error(f"⚠️ Nem találom a fájlt: {ALAP_FAJL}")
    st.stop()

# Oszlopok beazonosítása
nev_col = df.columns[0]
urt_col = next((c for c in df.columns if "urtartalom" in c.lower() or "űrtartalom" in c.lower()), df.columns[1])

# --- OLDALSÁV ---
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["Pult töltés", "Pult zárás", "Zárás véglegesítése", "Előzmények"])

if 'atmeneti_leltar' not in st.session_state: st.session_state.atmeneti_leltar = {}
if 'atmeneti_toltes' not in st.session_state: st.session_state.atmeneti_toltes = {}

# --- 1. FUNKCIÓ: PULT TÖLTÉS (KOMBINÁLT BEVITEL) ---
if funkcio == "Pult töltés":
    st.title("🚚 Pult töltés (Raktár -> Pult)")
    st.info("Itt egyszerre adhatsz meg kartont és darabot is!")
    kereses = st.text_input("🔍 Keresés termékre...", "", key="search_tolt")

    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", "megnevezés", "tétel", ""] or "unnamed" in nev.lower(): continue
        if kereses.lower() not in nev.lower(): continue

        urt_ertek = str(row[urt_col]).strip() if urt_col in row else "-"
        try:
            valto_szam = float(str(row.iloc[26]).replace(',', '.')) if not pd.isna(row.iloc[26]) else 1.0
        except: valto_szam = 1.0

        with st.container():
            st.markdown(f"### {nev}")
            # 4 oszlop: Infó, Karton bevitel, Darab bevitel, Összesen
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])
            
            with c1:
                st.write(f"📏 **Űrtartalom:** {urt_ertek}")
                st.caption(f"📦 **Kiszerelés:** {int(valto_szam)} db/karton")
            
            with c2:
                k_menny = st.number_input("Karton", min_value=0, step=1, key=f"t_kart_{idx}")
            
            with c3:
                d_menny = st.number_input("Darab", min_value=0, step=1, key=f"t_darab_{idx}")
            
            # Kiszámoljuk: (Karton * Váltószám) + plusz Darabok
            vegleges_db = (k_menny * valto_szam) + d_menny
            
            with c4:
                if vegleges_db > 0:
                    st.write("**Összesen:**")
                    st.info(f"{int(vegleges_db)} db")
                    st.session_state.atmeneti_toltes[nev] = vegleges_db
            st.divider()

# --- 2. FUNKCIÓ: PULT ZÁRÁS ---
elif funkcio == "Pult zárás":
    st.title("🍹 Pult zárás (Leltár)")
    kereses = st.text_input("🔍 Keresés...", "", key="search_zaras")

    for idx, row in df.iterrows():
        nev = str(row[nev_col]).strip()
        if nev.lower() in ["nan", "megnevezés", "tétel", ""] or "unnamed" in nev.lower(): continue
        if kereses.lower() not in nev.lower(): continue

        urt_ertek = str(row[urt_col]).strip() if urt_col in row else "-"
        kisz_ertek = str(row.iloc[26]).strip() if len(row) > 26 else "-"

        with st.container():
            st.markdown(f"### {nev}")
            c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.2])
            
            with c1:
                st.write(f"📏 **Űrtartalom:** {urt_ertek}")
                st.caption(f"📦 **Kiszerelés:** {kisz_ertek} db")
            
            with c2:
                mod = st.radio("Mód:", ["Teli (1.0)", "Bontott (0.25)"], key=f"mod_{idx}", horizontal=True)
                lepeskoz = 1.0 if "Teli" in mod else 0.25
            
            with c3:
                regi = st.session_state.atmeneti_leltar.get(nev, 0.0)
                uj = st.number_input("Darab", min_value=0.0, step=lepeskoz, key=f"zaras_{idx}", value=regi, format="%.2f")
                st.session_state.atmeneti_leltar[nev] = uj

            with c4:
                if uj > 0:
                    st.write("**Összesen:**")
                    formazott = f"{int(uj)}" if uj.is_integer() else f"{uj}"
                    st.info(f"{formazott} db")
            st.divider()

# --- 3. FUNKCIÓ: ZÁRÁS ÉS MENTÉS ---
elif funkcio == "Zárás véglegesítése":
    st.title("💾 Adatok rögzítése")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🚚 Mai töltések")
        toltes_lista = [{"Termék": k, "Mennyiség (db)": v} for k, v in st.session_state.atmeneti_toltes.items() if v > 0]
        if toltes_lista:
            st.table(pd.DataFrame(toltes_lista))
            if st.button("TÖLTÉS MENTÉSE"):
                t_df = pd.DataFrame(toltes_lista)
                t_df['Dátum'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                t_df.to_csv(ADATBAZIS_TOLTES, mode='a', index=False, header=not os.path.exists(ADATBAZIS_TOLTES))
                st.success("Mentve!")
                st.session_state.atmeneti_toltes = {}
    with col_b:
        st.subheader("🍹 Pult zárás")
        leltar_lista = [{"Termék": k, "Záró": v} for k, v in st.session_state.atmeneti_leltar.items() if v > 0]
        if leltar_lista:
            st.table(pd.DataFrame(leltar_lista))
            if st.button("LELTÁR MENTÉSE"):
                l_df = pd.DataFrame(leltar_lista)
                l_df['Dátum'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                l_df.to_csv(ADATBAZIS_ZARAS, mode='a', index=False, header=not os.path.exists(ADATBAZIS_ZARAS))
                st.success("Mentve!")
                st.session_state.atmeneti_leltar = {}

# --- 4. FUNKCIÓ: ELŐZMÉNYEK ---
elif funkcio == "Előzmények":
    st.title("📋 Adatbázisok")
    valasztas = st.radio("Melyik listát nézzük?", ["Töltések", "Zárások"], horizontal=True)
    fajl = ADATBAZIS_TOLTES if valasztas == "Töltések" else ADATBAZIS_ZARAS
    if os.path.exists(fajl):
        st.dataframe(pd.read_csv(fajl), use_container_width=True)