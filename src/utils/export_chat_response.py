"""
Module d'export des réponses générées par le modèle LLM pour un patient donné.

Ce module permet de récupérer toutes les réponses associées à une session,
de les concaténer proprement, et de les exporter dans un fichier Markdown.
Il peut également intégrer des graphiques de constantes si fournis.

Utilisé notamment pour générer des synthèses textuelles enrichies à partir
des sessions de chat dans l'application OBY-IA.
"""

# src/utils/export_chat_response.py

from pathlib import Path
from datetime import datetime
from fpdf import FPDF
from docx import Document
import os
from config.config import MARKDOWN_CHAT_EXPORTS


def export_llm_responses(session_manager_instance, session_id, patient_name, figs_list=None):
    """
        Exporte les réponses du LLM pour un patient donné dans un fichier Markdown.

        Cette fonction extrait l'ensemble des réponses associées à une session utilisateur
        via le gestionnaire de sessions, puis les enregistre dans un fichier `.md`
        dans un dossier structuré par patient et date. Elle peut également inclure
        des graphiques (figures Plotly) si fournis.

        Args:
            session_manager_instance : Instance de SessionManager utilisée pour accéder aux réponses.
            session_id (str) : Identifiant unique de la session.
            patient_name (str) : Nom du patient concerné par l'export.
            figs_list (list, optionnel) : Liste de graphiques (objets Plotly) à inclure dans le fichier.

        Returns:
            str : Chemin absolu du fichier Markdown généré.

        Raises:
            ValueError : Si aucune réponse du LLM n'est disponible pour la session donnée.
        """
    # Vérifications des arguments
    print("🔍 DÉMARRAGE EXPORT")
    print(f"📌 session_id: {session_id}")
    print(f"📌 patient_name: {patient_name}")


    # Récupérer toutes les réponses
    llm_responses = session_manager_instance.get_llm_responses(session_id)
    print(f"🧠 Nombre de réponses récupérées : {len(llm_responses)}")

    if not llm_responses:
        print("❌ Aucune réponse à exporter.")
        raise ValueError("Aucune réponse du LLM à exporter pour ce patient.")


    # Concatène les réponses avec des séparateurs pour plus de lisibilité
    final_text = "\n\n---\n\n".join(llm_responses)


    # Chemin d'export
    today = datetime.today().strftime("%Y-%m-%d")
    export_dir = MARKDOWN_CHAT_EXPORTS / patient_name / today
    export_dir.mkdir(parents=True, exist_ok=True)


    # Fichier final
    file_path = export_dir / f"export_chat_{patient_name}.md"


    # Écriture Markdown
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_text)

        # Si des figures sont fournies
        if figs_list:
            print(f'type(figs_list[0] --> "{type(figs_list[0])}")')
            f.write("\n\n## Graphique des constantes du patient\n\n")

            for i, fig in enumerate(figs_list):
                image_path = os.path.join(export_dir, f"{patient_name}_graph_{i + 1}.png")
                fig.write_image(image_path)
                f.write(f"![Graphique {i + 1}]({os.path.basename(image_path)})\n\n")


    print(f"✅ Export Markdown terminé : {file_path}")
    return str(file_path)

