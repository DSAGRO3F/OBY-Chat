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
import os
from config.config import MARKDOWN_CHAT_EXPORTS


def export_llm_responses(session_manager_instance, session_id, patient_name, figs_list=None):
    """
    Exporte l'historique complet des échanges (utilisateur + LLM) d'une session
    vers un fichier Markdown, avec option d'inclure des graphiques.

    Chaque interaction est formatée sous forme :
    - **Utilisateur** : question
    - **OBY-Chat** : réponse

    Args:
        session_manager_instance: Instance du gestionnaire de sessions.
        session_id (str): Identifiant unique de la session.
        patient_name (str): Nom du patient pour nommer le fichier exporté.
        figs_list (list, optional): Liste de chemins vers des fichiers image à inclure.

    Raises:
        ValueError: Si aucun historique n'est disponible à exporter.
    """

    session = session_manager_instance.get_session(session_id)
    if not session:
        raise ValueError("❌ Session introuvable pour l’export.")


    chat_history = session_manager_instance.get_chat_history(session_id)
    if not chat_history:
        raise ValueError("❌ Aucun échange enregistré dans cette session.")

    print(f"🧠 Nombre d’échanges récupérés : {len(chat_history)}")

    icon_user = "🧑‍⚕️"
    icon_llm = "🤖"
    formatted_exchanges = []

    final_text = ""
    for user_msg, llm_msg in chat_history:
        user_msg = (user_msg or "").strip()
        llm_msg = (llm_msg or "").strip()
        formatted = (
            f"### {icon_user} Utilisateur\n\n"
            f"> {user_msg}\n\n"
            f"**{icon_llm} Réponse OBY :**\n\n"
            f"{llm_msg}"
        )
        formatted_exchanges.append(formatted)

    final_text = "\n\n---\n\n".join(formatted_exchanges)

    # for user_input, model_response in chat_history:
    #     final_text += f"**Utilisateur** : {user_input}\n\n"
    #     final_text += f"**OBY-Chat** : {model_response}\n\n"
    #     final_text += "---\n\n"

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

