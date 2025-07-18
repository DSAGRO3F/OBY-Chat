"""
Module d'accès aux constantes médicales des patients depuis la base SQLite.

Ce module permet :
- d’identifier les constantes disponibles en base (poids, tension, etc.),
- de récupérer l’historique des valeurs d’un patient pour chaque constante.

Les données extraites sont retournées sous forme de DataFrames Pandas,
prêtes à être analysées ou visualisées dans l'application OBY-IA.
"""





import sqlite3
import pandas as pd
from config.config import DB_CONSTANTES_SANTE


# 1. Obtenir les tables disponibles
def get_available_constantes() -> list:
    """Retourne la liste des tables (constantes disponibles) dans la base SQLite."""
    conn = sqlite3.connect(DB_CONSTANTES_SANTE)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    conn.close()
    return tables




# 2. Extraire des tables les valeurs de constantes pour un patient donné.
def get_constantes_patient(nom: str) -> dict:
    """Retourne un dictionnaire de DataFrames pour toutes les constantes disponibles du patient."""
    conn = sqlite3.connect(DB_CONSTANTES_SANTE)
    constantes_data = {}
    constantes_list = get_available_constantes()

    print(f"🔍 Récupération des constantes pour le patient : {nom}")
    print(f"📋 Constantes disponibles en base : {constantes_list}")

    for constante in constantes_list:
        try:
            query = f"""
                SELECT date, valeur 
                FROM {constante} 
                WHERE LOWER(nom) = LOWER(?) 
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn, params=(nom,))

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors='coerce')
                df = df.dropna(subset=["date"]).sort_values(by="date")
                constantes_data[constante] = df

                print(f"✅ {constante} → {len(df)} lignes")
                print(df.head(2))  # aperçu facultatif
            else:
                print(f"⚠️ {constante} → aucune donnée pour {nom}")

        except sqlite3.Error as e:
            print(f"❌ Erreur SQL sur la table {constante}: {e}")

    conn.close()

    if not constantes_data:
        print(f"ℹ️ Aucune constante trouvée pour le patient '{nom}'.")

    return constantes_data