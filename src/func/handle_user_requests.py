# src/func/handle_user_requests.py
"""
Gestion des requêtes utilisateur pour OBY-IA (module Dash/API).

Ce module orchestre les deux temps de la conversation : requête initiale
(`handle_initial_request`) avec détection d’intention et question de confirmation,
puis traitement de la réponse de confirmation (`handle_confirmation_response`)
avec exécution du pipeline et construction de l’affichage final.
Les messages sont tagués (patient_key, user_id, msg_type) puis filtrés/retagués
pour éviter tout mélange d’historiques entre patients, et une vue prête à afficher
(`chat_history_display`) est renvoyée à l’UI lorsqu’un changement de patient survient.

"""

from dash import dcc, html
from typing import Literal

from src.llm_user_session.session_manager_instance import session_manager_instance
from src.func.generate_ppa_from_poa import process_ppa_request
from src.func.generate_structured_medical_plan import generate_structured_medical_plan
from src.func.llm_prompts import system_prompt, system_prompt_medical_plan
from src.func.extract_user_intent import detect_user_intent
from src.func.get_patient_constants_graphs import process_patient_request_with_constants
from src.func.extract_patient_name import extract_patient_name_llm
from src.func.serialize_figs import serialize_figs


# ================================================================================================ #
# --------------------- Fonctions accessoires --------------------- #
# ================================================================================================ #
from pathlib import Path
import re

def _normalize_key(s: str | None) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"\s+", "_", s)
    return s or "UNKNOWN"

def get_patient_key(nom: str | None = None, current_patient: str | None = None, patient_file_path: str | None = None) -> str:
    # Si on connaît déjà le fichier patient, on utilise cette clé
    if patient_file_path:
        try:
            return Path(patient_file_path).stem
        except Exception:
            pass
    # Sinon on normalise le nom détecté / patient courant
    return _normalize_key(nom or current_patient)

def tag_user_div(text: str, patient_key: str, user_id: str, msg_type: str):
    return html.Div(
        text,
        className="user-message",
        id={"type": "chat-msg", "patient_key": patient_key, "user_id": user_id, "msg_type": msg_type},
    )

def tag_bot_div_markdown(md_text: str, patient_key: str, user_id: str, msg_type: str):
    return html.Div(
        dcc.Markdown(md_text),
        className="bot-response",
        id={"type": "chat-msg", "patient_key": patient_key, "user_id": user_id, "msg_type": msg_type},
    )

def filter_history_by_patient_and_user(history: list, patient_key: str, user_id: str) -> list:
    kept = []
    for m in history:
        # dict API
        if isinstance(m, dict) and "props" not in m:
            if m.get("patient_key") == patient_key and m.get("user_id") == user_id:
                kept.append(m)
            continue
        # dict Dash sérialisé
        if isinstance(m, dict) and "props" in m:
            pid = m["props"].get("id", {})
            if isinstance(pid, dict) and pid.get("patient_key") == patient_key and pid.get("user_id") == user_id:
                kept.append(m)
            continue
        # objet Dash
        pid = getattr(m, "id", None)
        if isinstance(pid, dict) and pid.get("patient_key") == patient_key and pid.get("user_id") == user_id:
            kept.append(m)
    return kept

def retag_last_turn_by_type(prev_history: list, final_patient_key: str) -> None:
    """
    Retag la dernière confirm_prompt et la user_request qui la précède
    pour leur mettre patient_key = final_patient_key.
    """
    idx_confirm = None
    # trouver la dernière confirm_prompt
    for i in range(len(prev_history) - 1, -1, -1):
        _, _, mt = _extract_role_text_type(prev_history[i])
        if mt == "confirm_prompt":
            idx_confirm = i
            break
    if idx_confirm is None:
        return

    def _set_key(m):
        # dict API
        if isinstance(m, dict) and "props" not in m:
            m["patient_key"] = final_patient_key
            return
        # dict Dash sérialisé
        if isinstance(m, dict) and "props" in m:
            pid = m["props"].get("id")
            if isinstance(pid, dict):
                pid["patient_key"] = final_patient_key
            return
        # objet Dash
        pid = getattr(m, "id", None)
        if isinstance(pid, dict):
            pid["patient_key"] = final_patient_key

    _set_key(prev_history[idx_confirm])          # confirm_prompt
    if idx_confirm - 1 >= 0:
        _set_key(prev_history[idx_confirm - 1])  # user_request

def keep_last_request_plus_confirm(history_filtered: list) -> list:
    idx_confirm = None
    for i in range(len(history_filtered) - 1, -1, -1):
        _, _, mt = _extract_role_text_type(history_filtered[i])
        if mt == "confirm_prompt":
            idx_confirm = i
            break
    if idx_confirm is None:
        return history_filtered
    start = idx_confirm - 1
    for j in range(idx_confirm - 1, -1, -1):
        _, _, mt = _extract_role_text_type(history_filtered[j])
        if mt == "user_request":
            start = j
            break
    return history_filtered[max(start, 0): idx_confirm + 1]

def _extract_role_text_type(msg):
    """
    Retourne (role, text, msg_type) pour:
      - dict API: {'role', 'text'/'markdown', 'msg_type'}
      - dict Dash sérialisé: {'type','namespace','props':{id, className, children}}
      - objet Dash (html.Div/dcc.Markdown) en mémoire
    """
    # 1) dict API
    if isinstance(msg, dict) and "props" not in msg and ("role" in msg or "msg_type" in msg):
        role = msg.get("role")
        text = (msg.get("markdown") or msg.get("text") or "")
        mtyp = msg.get("msg_type")
        return role, str(text), mtyp

    # 2) dict Dash sérialisé (venant du dcc.Store)
    if isinstance(msg, dict) and "props" in msg:
        props = msg.get("props", {}) or {}
        className = props.get("className", "") or ""
        role = "assistant" if "bot-response" in className else ("user" if "user-message" in className else None)

        pid = props.get("id", {})
        mtyp = pid.get("msg_type") if isinstance(pid, dict) else None

        ch = props.get("children", None)
        # dcc.Markdown sérialisé -> {'type':'Markdown','props':{'children': '...'}}
        if isinstance(ch, dict) and "props" in ch:
            text = ch["props"].get("children", "")
        # parfois children peut être une liste (Dash sérialise des tableaux)
        elif isinstance(ch, list):
            # concat simple des fragments textuels
            text = " ".join(str(x) for x in ch if isinstance(x, (str, int, float)))
        else:
            text = ch if isinstance(ch, (str, int, float)) or ch is None else ""

        return role, str(text or ""), mtyp

    # 3) objet Dash (runtime)
    cls = getattr(msg, "className", "") or ""
    role = "assistant" if "bot-response" in cls else ("user" if "user-message" in cls else None)
    pid = getattr(msg, "id", None)
    mtyp = pid.get("msg_type") if isinstance(pid, dict) else None
    ch = getattr(msg, "children", None)
    if hasattr(ch, "children"):
        text = ch.children if ch.children is not None else ""
    else:
        text = ch if ch is not None else ""
    return role, str(text), mtyp

# Wrapper pour le code existant qui appelle encore _extract_role_and_text
def _extract_role_and_text(msg):
    role, text, _ = _extract_role_text_type(msg)
    return role, text

def _types(lst):
    return [_extract_role_text_type(m)[2] for m in (lst[-4:] if lst else [])]

def trim_to_last_confirmation_block(history: list) -> list:
    idx_confirm = None
    for i in range(len(history) - 1, -1, -1):
        role, text, mt = _extract_role_text_type(history[i])
        if mt == "confirm_prompt" or (role == "assistant" and "confirmez" in text.lower()):
            idx_confirm = i
            break
    if idx_confirm is None:
        return history
    start = idx_confirm - 1
    for j in range(idx_confirm - 1, -1, -1):
        r, _, mt = _extract_role_text_type(history[j])
        if mt == "user_request" or r == "user":
            start = j
            break
    return history[max(start, 0):]


# ================================================================================================ #
# --------------------- Fonctions appelées par handle_user_input_or_logout() --------------------- #
# ================================================================================================ #
# 1/.
def handle_initial_request(user_input, session,
                           session_data, chat_history,
                           current_patient, output_mode: Literal["dash", "api"] = "dash"):

    """
    - Prépare la phase pré-confirmation : détecte l’intention et le patient, met à jour la session et renvoie le delta d’affichage (requête + question de confirmation).
    - Paramètres:
        - user_input (str)
        - session (dict)
        - session_data (dict avec "user_id","session_id")
        - chat_history (list)
        - current_patient (str|None)
        - output_mode (Literal["dash","api"]).
    - Retourne un tuple:
        - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any|None).
    Ne lance aucun pipeline métier; lève ValueError si session_data est incomplet.
    Les messages ajoutés sont tagués (patient_key, user_id, msg_type).
    """

    # --- IDs fournis par l’UI ---
    user_id = (session_data or {}).get("user_id")
    session_id = (session_data or {}).get("session_id")
    if not user_id or not session_id:
        raise ValueError("session_data manquant: 'user_id' et/ou 'session_id'")

    # --- Récupérer/Créer la session côté serveur ---
    server_session = session_manager_instance.get_session(session_id)
    if server_session is None:
        session_manager_instance.create_session(user_id=user_id, session_id=session_id)
        server_session = session_manager_instance.get_session(session_id)

    # --- (Option) cohérence user_id ---
    if server_session.get("user_id") != user_id:
        user_id = server_session.get("user_id")

    # --- On retourne un DELTA uniquement ---
    chat_history = []

    # --- Logs & détection ---
    bot_response = None  # on n’appendra qu’un SEUL confirm_prompt plus bas
    print("🚀 handle_initial_request()")
    print(f'🟡 requête utilisateur {user_input}')

    intent_dict = detect_user_intent(user_input)
    nom = extract_patient_name_llm(user_input)
    intent = intent_dict.get("intent", "unknown")
    print(f'🟢 Intention détectée: {intent}')

    # --- Tag du message utilisateur ---
    nom_norm = (nom or "").strip()
    candidate_key = get_patient_key(nom=nom_norm, current_patient=current_patient)

    # 1) REQUÊTE (user)
    if output_mode == "dash":
        chat_history.append(
            tag_user_div(f"👤 {user_input.strip()}", candidate_key, user_id, "user_request")
        )
    else:
        chat_history.append({
            "role": "user",
            "text": user_input.strip(),
            "patient_key": candidate_key,
            "user_id": user_id,
            "msg_type": "user_request",
        })

    # 2) Construire le TEXTE FINAL de confirmation (une seule fois)
    if intent == "generate_ppa":
        text = "demande de génération de PPA"
        confirm_text = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"
    elif intent == "get_constants":
        text = "demande de constantes patient"
        confirm_text = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"
    elif intent == "generate_recommendations":
        text = "demande de recommandations de soins"
        confirm_text = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"
    else:
        confirm_text = (
            "❌ Cette demande ne peut pas être traitée par OBY-IA, car elle sort du cadre de l'accompagnement des personnes âgées.\n\n"
            "Voici quelques exemples de requêtes que vous pouvez utiliser :\n"
            "- *Prépare-moi le plan d’aide pour Madame Dupont*\n"
            "- *Montre-moi les constantes du patient Martin sur le dernier mois*\n"
            "- *Quelles sont les recommandations en cas d’AVC ?*"
        )

    # 3) DEMANDE DE CONFIRMATION (assistant) — une seule insertion
    if output_mode == "dash":
        chat_history.append(
            tag_bot_div_markdown(confirm_text, candidate_key, user_id, "confirm_prompt")
        )
    else:
        chat_history.append({
            "role": "assistant",
            "markdown": str(confirm_text),
            "patient_key": candidate_key,
            "user_id": user_id,
            "msg_type": "confirm_prompt",
        })

    # 4) Marquer la session (écriture IN-PLACE dans le dict du manager)
    server_session["intent_confirmation_pending"] = True
    server_session["intent_candidate"] = {
        "intent": intent,
        "name": nom_norm,
        "full_user_input": user_input,
    }

    # 5) (Option) historiser dans l’objet Session si tu l’utilises
    sess_obj = server_session.get("session_obj")
    if sess_obj:
        sess_obj.add_message(user_input, confirm_text)

    chat_history_display = None

    types = [_extract_role_text_type(m)[2] for m in chat_history]
    print(f"🟠 chat_history juste avant return (len={len(chat_history)}): types={types}")

    return chat_history, [], "", "", current_patient, [], chat_history_display


# 2/.
def handle_confirmation_response(user_input, session,
                                 session_data, chat_history,
                                 current_patient, output_mode: Literal["dash", "api"] = "dash"):

    """
   - Traite la réponse de confirmation (oui/non), exécute le pipeline demandé et prépare l’affichage.
   - Paramètres:
        - user_input (str)
        - session (dict)
        - session_data (dict avec "user_id","session_id")
        - chat_history (list, snapshot UI)
        - current_patient (str|None)
        - output_mode (Literal["dash","api"])
    - Filtre/retague l’historique par (patient_key, user_id), reconstruit la paire [user_request, confirm_prompt], ajoute le delta [confirm_answer, bot_response], gère le changement de patient et réinitialise les flags d’intention.
    - Retourne un tuple :
        - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any).
    - Lève ValueError si session_data est incomplet.
    """

    figs_list: list = []
    table_html = ""
    anomaly_block = ""
    serialized_figs = None
    figures_out: list = []
    bot_response: str = ""
    session_id = session_data["session_id"]

    # --- IDs fournis par l’UI ---
    user_id = (session_data or {}).get("user_id")
    session_id = (session_data or {}).get("session_id")
    if not user_id or not session_id:
        raise ValueError("session_data manquant: 'user_id' et/ou 'session_id'")

    # --- Récupérer/Créer la session côté serveur ---
    server_session = session_manager_instance.get_session(session_id)
    if server_session is None:
        session_manager_instance.create_session(user_id=user_id, session_id=session_id)
        server_session = session_manager_instance.get_session(session_id)

    # --- Etat historique complet avant reset pour delta ---
    prev_chat_history = list(chat_history) if chat_history else []

    # chat_history = delta des échanges
    chat_history = []

    # =======Debug: Vérification: ce que contient chat_history ===========
    # print(
    #     "🟠 prev_chat_history --Fn handle_conf_req-- len=", len(prev_chat_history),
    #     "tail types=",
    #     [_extract_role_text_type(m)[2] for m in (prev_chat_history[-4:] if prev_chat_history else [])]
    # )

    types = [_extract_role_text_type(m)[2] for m in prev_chat_history]
    print(f"🟠 prev_chat_history len={len(prev_chat_history)} types_tail={types[-4:]}")

    ok_pair = len(prev_chat_history) >= 2 and types[-2:] == ["user_request", "confirm_prompt"]

    if ok_pair:
        # (optionnel) log court des deux textes
        tu = _extract_role_text_type(prev_chat_history[-2])[1][:80].replace("\n", " ")
        ta = _extract_role_text_type(prev_chat_history[-1])[1][:80].replace("\n", " ")
        print(f"✅ paire OK -> user_request: {tu} | confirm_prompt: {ta}")
    else:
        print("🔴️ paire absente -> pas de user_request+confirm_prompt")

    # =================================================================================


    # Mise en place tag "switched" -> adapter texte affiché si changement patient
    filtered_prev_for_display: list = []
    chat_history_display: list | None = None
    switched = False

    # Initialisaiton
    intent_candidate = session.get("intent_candidate") or {}
    candidate_name = intent_candidate.get("name")

    # Initialisaiton patient_key
    patient_key = get_patient_key(
        nom=candidate_name or current_patient,
        current_patient=current_patient,
        patient_file_path=None
    )

    # Retag + filtre
    retag_last_turn_by_type(prev_chat_history, patient_key)
    filtered_prev_for_display = filter_history_by_patient_and_user(prev_chat_history, patient_key, user_id)
    print("🟠 filtered types=", _types(filtered_prev_for_display))


    # Récupération réponse utilisateur
    print('⚠️Confirmation attendue...')
    answer = user_input.strip().lower()
    dash_yes_text = f"👤 {answer}"
    api_yes_text = user_input.strip()

    # server_session["intent_confirmation_pending"]

    full_user_input = server_session["intent_candidate"]["full_user_input"]
    # print(f'⚠️handle_confirmation_response/full_user_input: {full_user_input}')


    # Intention confirmée, -> changement état de intent_confirmation_pending
    norm_answer = answer.replace("’", "'").strip().strip(" .!?,;:")
    if norm_answer in {"oui", "yes", "ok", "o", "y", "c'est bien ça"}:
        server_session["intent_confirmation_pending"] = False
        intent = server_session["intent_candidate"]["intent"]
        nom = server_session["intent_candidate"]["name"]

        patient_key = get_patient_key(
            nom=server_session.get("intent_candidate", {}).get("name") or nom or current_patient,
            current_patient=current_patient,
            patient_file_path=None
        )


        # Définition des flags
        ppa_requested = intent == "generate_ppa"
        constantes_requested = intent == "get_constants"
        recommandations_requested = intent == "generate_recommendations"
        print(f"✅ Intention confirmée par l’utilisateur : {intent}")

        print(f"🎯 Intentions détectées : "
              f"recommandations: {recommandations_requested},"
              f"constantes={constantes_requested}, "
              f"ppa={ppa_requested}, "
              f"nom patient={nom}")
        print(f'✅détection intention réussie')


        # On déclenche l'un des pipelines suivants selon l'intention détectée
        # --- Réinitialisation si changement de patient ---
        if nom and (ppa_requested or constantes_requested or recommandations_requested):
            if nom != current_patient:
                print(f"🔴 Changement de patient détecté : {current_patient} ➡️ {nom}")
                switched = True

                # harmoniser le DERNIER couple vers la clé FINALE du patient
                retag_last_turn_by_type(prev_chat_history, patient_key)

                # filtrer le snapshot par patient+user
                filtered_prev_for_display = filter_history_by_patient_and_user(prev_chat_history, patient_key, user_id)
                print("✅ filtered_prev_for_display:",
                      [(_extract_role_text_type(m)[2]) for m in filtered_prev_for_display])
                # attendu: ["user_request", "confirm_prompt"]

                # ne garder QUE le dernier couple [user_request, confirm_prompt]
                filtered_prev_for_display = keep_last_request_plus_confirm(filtered_prev_for_display)

                # ajouter le "oui" (delta), tagué
                if output_mode == "dash":
                    chat_history.append(tag_user_div(f"👤 {answer}", patient_key, user_id, "confirm_answer"))
                else:
                    chat_history.append({"role": "user", "text": user_input.strip(),
                                         "patient_key": patient_key, "user_id": user_id, "msg_type": "confirm_answer"})


                # Reset UI de l’ancien patient + MAJ état
                figs_list = []
                table_html = ""
                anomaly_block = ""
                current_patient = nom
                session_manager_instance.reset_anonymization_mapping(user_id)
                session_manager_instance.set_current_patient(session_id, nom)

            else:
                print(f"✅ Patient conservé : {current_patient}")
                answer_raw = (user_input or "").strip()
                dash_yes_text = f"👤 {answer_raw}"
                if output_mode == "dash":
                    user_msg = tag_user_div(dash_yes_text, patient_key, user_id, "confirm_answer")
                else:
                    user_msg = {
                        "role": "user",
                        "text": answer_raw,
                        "patient_key": patient_key,
                        "user_id": user_id,
                        "msg_type": "confirm_answer",
                    }

                chat_history.append(user_msg)

        # --- Traitement des constantes ---
        if constantes_requested:
            try:
                print("✅ Appel à process_patient_request_with_constants()")
                bot_response, figs_list, table_html, anomaly_block = process_patient_request_with_constants(nom)

                if output_mode == "dash":
                    # ✅ Mode UI Dash: sérialisation pour dcc.Store
                    serialized_figs = serialize_figs(figs_list)
                    figures_out = figs_list  # pour construire dcc.Graph côté callback
                else:
                    # ✅ Mode API: JSON Plotly directement exploitable côté OBY
                    figures_out = [fig.to_plotly_json() for fig in figs_list]
                    serialized_figs = None

            except Exception as e:
                print(f"❌ Erreur dans process_patient_request_with_constants : {e}")
                bot_response = "Une erreur est survenue pendant le traitement des constantes."
                figs_list, table_html, anomaly_block = [], "", ""


                # --- Traitement demande PPA ---
        elif ppa_requested:
            print("✅ Appel à process_ppa_request() pour le PPA")
            try:
                bot_response, dict_mapping = process_ppa_request(full_user_input, system_prompt)

                # Enregistrer le mapping renvoyé par la fonction dans la session
                # Le récupérer proprement via session_manager.get_anonymization_mapping()
                session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

                # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
                session_manager_instance.append_llm_response(session_id, bot_response)

                # ✅ Ajout échange complet (question + réponse)
                session = session_manager_instance.get_session(session_id)
                session_obj = session.get("session_obj")
                if session_obj:
                    session_obj.add_message(user_input, bot_response)

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans process_ppa_request : {e}")
                bot_response = "Une erreur est survenue pendant la génération du PPA."
                figs_list, table_html, anomaly_block = [], "", ""


        # --- Traitement demande plan de soins ---
        elif recommandations_requested:
            print("✅ Appel à generate_structured_medical_plan() pour plan de soins")
            try:
                bot_response, dict_mapping = generate_structured_medical_plan(full_user_input,
                                                                              system_prompt_medical_plan)

                # Enregistrer le mapping renvoyé par la fonction dans la session
                # Le récupérer proprement via session_manager.get_anonymization_mapping()
                session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

                # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
                print("🔴before -> session_manager_instance.append_llm_response(session_id, bot_response")
                session_manager_instance.append_llm_response(session_id, bot_response)
                print("🔴after -> session_manager_instance.append_llm_response(session_id, bot_response")

                # ✅ Ajouter l’échange complet (question + réponse)
                print("🔴before -> session_manager_instance.get_session(session_id)")
                session = session_manager_instance.get_session(session_id)
                print("🔴after -> session_manager_instance.get_session(session_id)")
                session_obj = session.get("session_obj")
                if session_obj:
                    print("🔴before -> session_obj.add_message(user_input, bot_response)")
                    session_obj.add_message(user_input, bot_response)
                    print("🔴after -> session_obj.add_message(user_input, bot_response)")

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans generate_structured_medical_plan : {e}")
                bot_response = "Une erreur est survenue pendant l'extraction des recommandations de soins."
                figs_list, table_html, anomaly_block = [], "", ""


    else:
        # Rejet de l’intention
        session["intent_confirmation_pending"] = False
        session["intent_candidate"] = {"intent": None, "name": None, "full_user_input": ""}

        bot_response = (
            "Compris. Voici quelques exemples de requêtes que vous pouvez utiliser :\n"
            "- *Prépare-moi le plan d’aide pour Madame Dupont*\n"
            "- *Montre-moi les constantes du patient Martin sur le dernier mois*\n"
            "- *Quelles sont les recommandations en cas d’AVC ?*"
        )

    if bot_response:
        if output_mode == "dash":
            chat_history.append(tag_bot_div_markdown(str(bot_response), patient_key, user_id, "bot_response"))
        else:
            chat_history.append({
                "role": "assistant",
                "markdown": str(bot_response),
                "patient_key": patient_key,
                "user_id": user_id,
                "msg_type": "bot_response",
            })


    if switched:
        chat_history_display = filtered_prev_for_display + chat_history
    else:
        chat_history_display = None

    print("✅ delta types:",
          [(_extract_role_text_type(m)[2]) for m in chat_history])
    # attendu: ["confirm_answer", "bot_response"] (si le bot a répondu)

    return (chat_history, figures_out, table_html,
            anomaly_block, current_patient,
            serialized_figs, chat_history_display)
