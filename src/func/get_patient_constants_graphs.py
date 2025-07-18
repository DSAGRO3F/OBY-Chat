"""
Module d'analyse et de visualisation des constantes médicales des patients.

Ce module permet :
- de convertir les constantes brutes issues de la base de données en DataFrame,
- de détecter des anomalies selon des seuils définis,
- de générer des graphiques Plotly (poids, tension, température...),
- de produire des tableaux HTML interactifs pour Dash,
- de centraliser le traitement dans une fonction complète pour l’interface.

Utilisé notamment dans la page chatbot_ui de l’application OBY-IA.
"""



import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
from datetime import timedelta
from datetime import datetime
import os
import plotly.graph_objects as go
import tabulate

from src.data.get_constants import get_constantes_patient
# from src.func.extract_patient_name import extract_patient_name_llm
# from src.func.convert_constants_to_dataframe import convert_constants_to_dataframe




# 1. Conversion du dictionnaire brut en DataFrame
def convert_constants_to_dataframe(constants_dict):
    """
    Convertit un dictionnaire brut de constantes médicales en un DataFrame fusionné.

    Pour la tension, sépare les valeurs systolique/diastolique.
    Pour les autres constantes, convertit les valeurs en numérique.

    Args:
        constants_dict (dict): Dictionnaire {constante: DataFrame} pour un patient.

    Returns:
        pd.DataFrame: DataFrame fusionné avec toutes les constantes disponibles.
    """

    frames = []
    for key, df in constants_dict.items():
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        if key.lower() == "tension":
            df["valeur"] = df["valeur"].astype(str)
            df = df[df["valeur"].str.count("/") == 1].copy()

            if df.empty:
                print(f"⚠️ Aucune donnée de tension exploitable pour '{key}' — on saute.")
                continue

            split_df = df["valeur"].str.split("/", expand=True)

            if split_df.shape[1] != 2:
                print("❌ Format tension invalide après split :")
                print(split_df.head())
                continue

            df[["tension_sys", "tension_dia"]] = split_df.astype(float)
            df = df[["date", "tension_sys", "tension_dia"]]

        else:
            df[key] = pd.to_numeric(df["valeur"], errors="coerce")
            df = df[["date", key]]


        frames.append(df)
    print(f'Vérif frame_0 dans fonction convert_constants_to_dataframe, shape: {frames[0].shape}, isnull: {frames[0].isnull().sum()}')
    print(f'Vérif frame_1 dans fonction convert_constants_to_dataframe, shape: {frames[1].shape}, isnull: {frames[1].isnull().sum()}')

    df_merged = frames[0]
    for df in frames[1:]:
        df_merged = pd.merge(df_merged, df, on="date", how="outer")

    df_merged = df_merged.sort_values("date").reset_index(drop=True)
    print(f'columns in df_merged.columns: {df_merged.columns}')
    return df_merged




# 2. Analyse simple des constantes
def analyze_constants(df):
    """
    Analyse les constantes pour détecter des valeurs anormales.

    Compare les valeurs observées à des seuils définis (poids, température, tension).
    Marque les anomalies dans le DataFrame et produit un résumé textuel.

    Args:
        df (pd.DataFrame): Données des constantes fusionnées.

    Returns:
        Tuple[str, str]: (Tableau markdown des données + colonnes _anormal, résumé des anomalies)
    """

    anomalies = []
    seuils = {
        "poids": (45, 100),
        "température": (36.0, 38.0),
        "tension_sys": (90, 140),
        "tension_dia": (60, 90),
    }

    df_analyzed = df.copy()
    for col, (min_val, max_val) in seuils.items():
        if col in df:
            df_analyzed[f"{col}_anormal"] = ~df[col].between(min_val, max_val)
            n_anomalies = df_analyzed[f"{col}_anormal"].sum()
            if n_anomalies > 0:
                anomalies.append(f"🔴 {col} : {n_anomalies} valeur(s) anormale(s) détectée(s)")

    summary = "\n".join(anomalies) if anomalies else "✅ Aucune anomalie détectée sur les constantes."
    return df_analyzed.to_markdown(index=False), summary





# 3. Création des graphiques Plotly
def generate_graphs(df):
    """
    Génère des graphiques interactifs Plotly pour les constantes médicales.

    Args:
        df (pd.DataFrame): Données des constantes.

    Returns:
        list: Liste de composants Dash contenant les graphiques.
    """

    graphs = []

    if "poids" in df:
        fig = px.line(df, x="date", y="poids", title="Évolution du poids")
        graphs.append(dcc.Graph(figure=fig))

    if "température" in df:
        fig = px.line(df, x="date", y="température", title="Évolution de la température")
        graphs.append(dcc.Graph(figure=fig))

    if "tension_sys" in df and "tension_dia" in df:
        fig = px.line(df, x="date", y=["tension_sys", "tension_dia"], title="Tension artérielle")
        graphs.append(dcc.Graph(figure=fig))

    return graphs





# 4. Format DataFrame en DataTable Dash
def generate_constants_table(df):
    """
    Crée une table interactive Dash à partir d'un DataFrame de constantes.

    Args:
        df (pd.DataFrame): Données des constantes.

    Returns:
        dash_table.DataTable: Table interactive à afficher dans l'interface.
    """

    return dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center", "fontSize": 14}
    )





# 5. Fonction principale appelée depuis chatbot_ui
def process_patient_request_with_constants(nom):
    """
    Pipeline complet de traitement des constantes d’un patient pour l’interface Dash.

    Charge les données depuis la base, construit les visualisations, détecte les anomalies
    et génère les blocs HTML à afficher dans l’application.

    Args:
        nom (str): Nom du patient.

    Returns:
        Tuple[str, list, html.Div, html.Div]:
            - Message texte pour le chatbot
            - Liste de graphiques Plotly
            - Tableau HTML des constantes
            - Bloc Markdown avec l’analyse des tendances
    """

    print(f"📊 [INFO] Récupération des constantes pour {nom}")
    constantes_dict = get_constantes_patient(nom)

    if not constantes_dict:
        return (
            f"ℹ️ Aucune donnée de constantes trouvée pour le patient {nom}.",
            [],
            html.Div("Aucune donnée de constantes disponible."),
            html.Div("Aucune anomalie détectée car aucune constante n’est disponible.")
        )

    df = convert_constants_to_dataframe(constantes_dict)
    print(f"✅ Constantes disponibles dans df.columns : {df.columns.tolist()}")

    figs = []

    # Poids
    if "poids" in df.columns:
        fig = px.line(df, x="date", y="poids", title="Évolution du poids", markers=True)
        figs.append(fig)

    # Tension artérielle
    if {"tension_sys", "tension_dia"}.issubset(df.columns):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["tension_sys"], mode='lines+markers', name="Systolique"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["tension_dia"], mode='lines+markers', name="Diastolique"))
        fig.update_layout(title="Évolution de la tension artérielle", xaxis_title="Date", yaxis_title="mmHg")
        figs.append(fig)

    # Fréquence cardiaque
    if "frequence_cardiaque" in df.columns:
        fig = px.line(df, x="date", y="frequence_cardiaque", title="Fréquence cardiaque", markers=True)
        figs.append(fig)

    # Température
    if "temperature" in df.columns:
        fig = px.line(df, x="date", y="temperature", title="Température corporelle", markers=True)
        figs.append(fig)

    # Génération du tableau Markdown
    table_md = df.to_markdown(index=False)
    table_html = html.Div([
        html.H5("Tableau des constantes"),
        html.Pre(table_md)
    ])

    # Analyse des constantes
    anomalies_md = analyze_constants(df)  # on suppose que cela retourne du Markdown déjà formaté
    anomaly_block = html.Div([
        html.H5("Analyse des tendances et anomalies"),
        dcc.Markdown(anomalies_md)
    ])

    # Réponse texte brute pour le chat (résumé court)
    texte = f"Voici les constantes de santé disponibles pour {nom}, accompagnées de leur visualisation et analyse."

    return texte, figs, table_html, anomaly_block















