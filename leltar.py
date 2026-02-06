import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- KONFIGURÁCIÓ ---
ALAP_FAJL = "lotusz_alap.csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdubKmAj92ODOhGb6VeWoloC_evzS5iuYxyV9WPdM8GHd4ikmOW_TJ0j3oDVGMvBi-/exec"

st.set_page_config(page_title="Lótusz Kontroll", layout="wide")

# MENÜ
st.sidebar.title("⚓ Lótusz Menü")
funkcio = st.sidebar.radio("Válassz:", ["📦 Raktár / Beszállítás", "🚚 Pult töltés", "🍹 Pult zárás", "💾 Mentés és Összesítés"])

# --- RAKTÁR ÉS BESZÁLLÍTÁS ---
if funkcio == "📦 Raktár / Beszállítás":
    st.title("📦 Raktár Készlet és Beszállítás")
    st.write("Itt rögzítheted, ha áru érkezik a nagykerből a raktárba.")
    
    # Itt most egy egyszerű beviteli mező van, de a Google-ből is olvashatnánk
    termek = st.selectbox("Válassz terméket:", pd.read_csv(ALAP_FAJL).iloc[:, 0])
    mennyiseg = st.number_input("Beérkezett mennyiség (db)", min_value=0, step=1)
    
    if st.button("Beszállítás rögzítése a Raktárba"):
        adat = [{"Termék": termek, "db": mennyiseg, "Idő": datetime.now().strftime("%Y-%m-%d %H:%M")}]
        payload = {"sheet": "Raktar", "rows": adat}
        res = requests.post(SCRIPT_URL, json=payload)
        if res.status_code == 200:
            st.success(f"Beérkezett: {mennyiseg} db {termek}")

# --- PULT TÖLTÉS (Ami levon a raktárból) ---
elif funkcio == "🚚 Pult töltés":
    st.title("🚚 Pult töltés (Raktár -> Pult)")
    # ... (A korábbi töltés kódod marad, de a véglegesítésnél a Toltesek fülre küldjük)
    st.info("A 'Beküldés' gomb megnyomásakor a rendszer automatikusan levonja ezeket a tételeket a Raktár készletéből.")
    # (Ide jön a korábbi Pult töltés logikád)

# --- MENTÉS ÉS ÖSSZESÍTÉS ---
elif funkcio == "💾 Mentés és Összesítés":
    st.title("💾 Napi adatok beküldése")
    # Itt jelenítjük meg a listát mielőtt a Google-be kerül
    if st.button("MAI MOZGÁSOK VÉGLEGESÍTÉSE"):
        # Itt hívjuk meg a SCRIPT_URL-t
        st.write("Adatok küldése és raktárkészlet frissítése...")
