import pandas as pd
import requests
import streamlit as st

API_URL = "http://api:8087/"  # URL du service API avec le préfixe correspondant à Traefik

st.title("🏆 Balloon de Oro")

# Affichage des boutons de vote
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Mbappe"):
        response = requests.post(f"{API_URL}/log-click/Mbappe")
        if response.ok:
            st.success("Vote enregistré!")

with col2:
    if st.button("Neymar"):
        response = requests.post(f"{API_URL}/log-click/Neymar")
        if response.ok:
            st.success("Vote enregistré!")

with col3:
    if st.button("Messi"):
        response = requests.post(f"{API_URL}/log-click/Messi")
        if response.ok:
            st.success("Vote enregistré!")

# Affichage des statistiques
st.subheader("📊 Statistiques des votes")
stats_response = requests.get(f"{API_URL}/stats")
if stats_response.ok:
    stats_data = stats_response.json()
    stats_df = pd.DataFrame(stats_data)
    if not stats_df.empty:
        stats_df.columns = ["Joueur", "Nombre de votes"]
        st.bar_chart(stats_df.set_index("Joueur"))
        st.table(stats_df)

# Affichage des derniers votes
st.subheader("🕒 Derniers votes")
clicks_response = requests.get(f"{API_URL}/clicks")
if clicks_response.ok:
    clicks_data = clicks_response.json()
    if clicks_data:
        clicks_df = pd.DataFrame(clicks_data)
        clicks_df.columns = ["Joueur", "Date du vote"]
        st.table(clicks_df)
