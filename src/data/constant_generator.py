"""
Module de génération de données fictives pour les constantes médicales.

Ce module permet de créer une base SQLite contenant des données simulées pour plusieurs types
de constantes de santé : poids, tension artérielle, fréquence cardiaque et température.

Les données sont générées automatiquement pour un ensemble de patients fictifs,
sur une période de 16 semaines, afin de servir de base de tests dans l'application OBY-IA.
"""




# Création des tables.
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random


def generate_database(db_path="constantes_sante.db"):
  """
  Crée une base SQLite avec des constantes médicales simulées.

  Cette fonction :
  - crée (ou remplace) les tables `poids`, `tension`, `frequence_cardiaque`, `temperature`,
  - insère des données fictives pour plusieurs patients sur 16 semaines glissantes,
  - stocke toutes les valeurs sous forme de texte pour uniformiser les formats.

  Args:
      db_path (str) : Chemin vers le fichier SQLite à créer ou mettre à jour. Par défaut : "constantes_sante.db".
  """

  conn = sqlite3.connect(db_path)
  cur = conn.cursor()

  tables = ["poids", "tension", "frequence_cardiaque", "temperature"]
  for table in tables:
    cur.execute(f"DROP TABLE IF EXISTS {table}")

    cur.execute(f"""
          CREATE TABLE IF NOT EXISTS {table} (
              patient_id INTEGER,
              nom TEXT,
              date TEXT,
              valeur TEXT  -- On met TEXT pour gérer les tensions '120/80'
          )
      """)

  patients = ["Deloin", "Leclerc", "Bernard"]
  start_date = datetime.today() - timedelta(weeks=16)

  for table in tables:
    for nom in patients:
      for i in range(16):
        current_date = start_date + timedelta(weeks=i)
        date = current_date.strftime("%Y-%m-%d")

        if table == "poids":
          valeur = round(random.uniform(60, 100), 1)
        elif table == "tension":
          # 🎯 Génération de la tension systolique/diastolique
          systolique = random.randint(100, 140)
          diastolique = random.randint(60, 90)
          valeur = f"{systolique}/{diastolique}"  # Format texte "120/80"
        elif table == "frequence_cardiaque":
          valeur = round(random.uniform(70, 130), 1)
        else:  # température
          valeur = round(random.uniform(35, 39), 1)

        print(f"[INSERT] table={table}, nom={nom}, date={date}, valeur={valeur}")

        cur.execute(
          f"INSERT INTO {table} (patient_id, nom, date, valeur) VALUES (?, ?, ?, ?)",
          (patients.index(nom), nom, date, str(valeur))  # ⚠️ On stocke tout en string pour uniformiser
        )

  print(f"[✔] Insertion {table} - {nom} - {date} - {valeur}")

  conn.commit()
  conn.close()

  if __name__ == "__main__":
    print("📦 Génération complète de la base de données santé.")
    generate_database()

